#!/usr/bin/env python3
"""
Process debate results → microsimulation → welfare → exhibits.
Can run on Round 0 consensus (preliminary) or full debate consensus (final).

Usage:
    python process_results.py [--round0]  # use Round 0 only
    python process_results.py              # use full debate results
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("process_results")


def extract_consensus(debate_dir: str = "output/debate", round0_only: bool = False):
    """Extract consensus design parameters from debate output."""
    from debate.parser import extract_parameters
    from debate.convergence import ConvergenceTracker

    domains = [
        "clinical_model", "payment_structure", "provider_rates", "org_structure",
        "regulatory_pathway", "quality_framework", "ai_architecture", "human_oversight",
        "sdoh_integration", "rural_urban", "anti_monopoly", "ethical_governance",
    ]

    if not round0_only:
        results_path = Path(debate_dir) / "debate_results.json"
        if results_path.exists():
            with open(results_path) as f:
                results = json.load(f)
            consensus = results.get("consensus_design", {})
            convergence_history = results.get("convergence_history", {})
            logger.info(f"Loaded full debate results: {results.get('total_rounds')} rounds, "
                       f"converged={results.get('converged')}")
            return consensus, convergence_history

    # Fall back to Round 0
    round0_path = Path(debate_dir) / "round_0.json"
    if not round0_path.exists():
        logger.error("No debate data found. Run the debate first.")
        sys.exit(1)

    with open(round0_path) as f:
        data = json.load(f)

    parsed = {}
    for agent_id, proposal in data["proposals"].items():
        parsed[agent_id] = extract_parameters(proposal, domains)
        logger.info(f"  {agent_id}: {len(parsed[agent_id].values)} params")

    tracker = ConvergenceTracker(domains, cv_threshold=0.15, domains_required=10, stability_rounds=2)
    cv_scores = tracker.compute_round_cv(parsed)
    consensus = tracker.compute_consensus(parsed)
    convergence_history = {d: [cv_scores.get(d, float("nan"))] for d in domains}

    converged = sum(1 for cv in cv_scores.values() if cv < 0.15)
    logger.info(f"Round 0 consensus: {converged}/12 domains converged")

    return consensus, convergence_history


def print_consensus_summary(consensus: dict):
    """Print key consensus parameters."""
    key_params = [
        ("clinical_model.ai_encounter_share", "AI Encounter Share", "%"),
        ("clinical_model.escalation_threshold", "Escalation Threshold", ""),
        ("payment_structure.capitation_rate", "Capitation Rate", ""),
        ("payment_structure.mlr_target", "MLR Target", "%"),
        ("provider_rates.pcp_rate_pct_medicare", "PCP Rate (% Medicare)", "%"),
        ("org_structure.org_type", "Organization Type", ""),
        ("regulatory_pathway.waiver_type", "Waiver Type", ""),
        ("quality_framework.hedis_reporting", "HEDIS Reporting", ""),
        ("ai_architecture.model_count", "AI Model Count", ""),
        ("human_oversight.supervision_ratio", "Supervision Ratio", ""),
        ("sdoh_integration.chw_per_1000", "CHWs per 1,000", ""),
        ("ethical_governance.audit_frequency", "Audit Frequency", ""),
    ]
    logger.info("=== KEY CONSENSUS PARAMETERS ===")
    for key, label, unit in key_params:
        val = consensus.get(key, "N/A")
        logger.info(f"  {label}: {val}{unit}")


def run_microsim(consensus: dict, n_iterations: int = 1000, output_dir: str = "output"):
    """Run microsimulation using consensus parameters."""
    from microsim.population import load_population
    from microsim.channels import run_psa, summarize_psa

    df = load_population()
    logger.info(f"Population: {len(df)} individuals")

    results_df = run_psa(
        df,
        n_iterations=n_iterations,
        scenarios=["sq_mco", "ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic",
                    "enhanced_ffs", "ai_aco_universal"],
        seed=42,
    )

    summary = summarize_psa(results_df)

    outdir = Path(output_dir) / "microsim"
    outdir.mkdir(parents=True, exist_ok=True)
    results_df.to_parquet(outdir / "psa_results_full.parquet", index=False)
    summary.to_csv(outdir / "psa_summary.csv", index=False)

    logger.info(f"PSA complete: {len(results_df)} scenario-iterations")

    # Print key results
    for _, row in summary.iterrows():
        logger.info(
            f"  {row['scenario']}: PMPM=${row['pmpm_mean']:.0f} "
            f"[{row['pmpm_p2.5']:.0f}-{row['pmpm_p97.5']:.0f}], "
            f"Hosp={row['hosp_per_1000_mean']:.0f}/1000, "
            f"HEDIS={row['hedis_gap_closure_mean']:.1%}"
        )

    return results_df, summary


def run_welfare(summary: pd.DataFrame, psa_results: pd.DataFrame, output_dir: str = "output"):
    """Run welfare analysis."""
    from microsim.welfare import compute_welfare, compute_equity_weighted_welfare, sensitivity_wtp

    welfare = compute_welfare(summary)
    equity_welfare = compute_equity_weighted_welfare(psa_results, epsilon=1.0)
    wtp_sensitivity = sensitivity_wtp(summary)

    outdir = Path(output_dir) / "welfare"
    outdir.mkdir(parents=True, exist_ok=True)
    welfare.to_csv(outdir / "welfare_analysis.csv", index=False)
    equity_welfare.to_csv(outdir / "equity_weighted_welfare.csv", index=False)
    wtp_sensitivity.to_csv(outdir / "wtp_sensitivity.csv", index=False)

    logger.info("=== WELFARE ANALYSIS ===")
    for _, row in welfare.iterrows():
        logger.info(
            f"  {row['scenario']}: PMPM savings=${row['pmpm_savings']:.1f}, "
            f"QALYs/1000={row['qaly_gain_per_1000']:.2f}, "
            f"B-W gap Δ={row['bw_hosp_gap_reduction']:.1f}"
        )

    return welfare, equity_welfare


def run_visualization(summary, welfare, psa_results, convergence_history, output_dir="output"):
    """Generate manuscript exhibits."""
    from visualization.exhibits import (
        plot_convergence_heatmap,
        plot_outcome_radar,
        plot_equity_impact,
        plot_welfare_waterfall,
    )

    figdir = Path(output_dir) / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    if convergence_history:
        plot_convergence_heatmap(convergence_history, figdir / "exhibit1_convergence.pdf")
        logger.info("  Exhibit 1: Convergence heatmap saved")

    plot_outcome_radar(summary, figdir / "exhibit2_outcomes.pdf")
    logger.info("  Exhibit 2: Outcome radar saved")

    plot_equity_impact(psa_results, figdir / "exhibit3_equity.pdf")
    logger.info("  Exhibit 3: Equity impact saved")

    plot_welfare_waterfall(welfare, figdir / "exhibit4_welfare.pdf")
    logger.info("  Exhibit 4: Welfare waterfall saved")

    logger.info(f"All figures saved to {figdir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round0", action="store_true", help="Use Round 0 consensus only")
    parser.add_argument("--n-iterations", type=int, default=1000, help="PSA iterations")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    # Step 1: Extract consensus
    consensus, convergence_history = extract_consensus(
        debate_dir=f"{args.output_dir}/debate",
        round0_only=args.round0,
    )
    print_consensus_summary(consensus)

    # Step 2: Microsimulation
    psa_results, summary = run_microsim(consensus, args.n_iterations, args.output_dir)

    # Step 3: Welfare
    welfare, equity_welfare = run_welfare(summary, psa_results, args.output_dir)

    # Step 4: Visualization
    try:
        run_visualization(summary, welfare, psa_results, convergence_history, args.output_dir)
    except ImportError as e:
        logger.warning(f"Visualization skipped: {e}")

    logger.info("Processing complete.")


if __name__ == "__main__":
    main()
