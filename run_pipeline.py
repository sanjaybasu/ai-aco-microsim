#!/usr/bin/env python3
"""
AI ACO Full Pipeline
====================
Runs the complete AI ACO analysis:
    1. Multi-agent debate → consensus design
    2. Microsimulation PSA → outcome estimates
    3. Welfare analysis → social surplus comparison
    4. Visualization → exhibits for manuscript

Usage:
    python run_pipeline.py [--debate-only] [--microsim-only] [--n-iterations 1000]
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
logger = logging.getLogger("ai_aco_pipeline")


def run_debate(output_dir: str = "output"):
    """Step 1: Run multi-agent debate."""
    from debate.engine import DebateEngine, DebateConfig, LLMConfig

    config = DebateConfig(
        max_rounds=6,
        convergence_cv_threshold=0.15,
        convergence_domains_required=10,
        convergence_stability_rounds=2,
        critique_sample_size=3,
        output_dir=f"{output_dir}/debate",
        llm=LLMConfig(
            provider="anthropic",
            model_id="claude-sonnet-4-20250514",
            temperature=0.7,
            max_tokens=4096,
        ),
    )

    engine = DebateEngine(config)
    results = engine.run()

    logger.info(f"Debate completed in {results['total_rounds']} rounds")
    logger.info(f"Converged: {results['converged']}")
    logger.info(f"Converged domains: {results['final_converged_domains']}")

    return results


def run_microsim(n_iterations: int = 1000, output_dir: str = "output"):
    """Step 2: Run microsimulation PSA."""
    from microsim.population import load_population
    from microsim.channels import run_psa, summarize_psa

    df = load_population()
    logger.info(f"Population: {len(df)} individuals")

    results_df = run_psa(
        df,
        n_iterations=n_iterations,
        scenarios=["sq_mco", "ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic",
                    "enhanced_ffs", "ai_aco_universal", "admin_only"],
        seed=42,
    )

    summary = summarize_psa(results_df)

    # Save
    outdir = Path(output_dir) / "microsim"
    outdir.mkdir(parents=True, exist_ok=True)
    results_df.to_parquet(outdir / "psa_results_full.parquet", index=False)
    summary.to_csv(outdir / "psa_summary.csv", index=False)

    logger.info(f"PSA complete: {len(results_df)} scenario-iterations")
    logger.info(f"Summary saved to {outdir / 'psa_summary.csv'}")

    return results_df, summary


def run_welfare(summary: pd.DataFrame, psa_results: pd.DataFrame, output_dir: str = "output"):
    """Step 3: Welfare analysis."""
    from microsim.welfare import compute_welfare, compute_equity_weighted_welfare, sensitivity_wtp

    welfare = compute_welfare(summary)
    equity_welfare = compute_equity_weighted_welfare(psa_results, epsilon=1.0)
    wtp_sensitivity = sensitivity_wtp(summary)

    outdir = Path(output_dir) / "welfare"
    outdir.mkdir(parents=True, exist_ok=True)
    welfare.to_csv(outdir / "welfare_analysis.csv", index=False)
    equity_welfare.to_csv(outdir / "equity_weighted_welfare.csv", index=False)
    wtp_sensitivity.to_csv(outdir / "wtp_sensitivity.csv", index=False)

    logger.info("Welfare analysis complete")
    for _, row in welfare.iterrows():
        logger.info(
            f"  {row['scenario']}: PMPM savings=${row['pmpm_savings']:.1f}, "
            f"Admin Δ={row['admin_cost_reduction_pp']:.1%}, "
            f"Hosp Δ={row['hosp_reduction_per_1000']:.1f}/1000"
        )

    return welfare, equity_welfare


def run_visualization(
    summary: pd.DataFrame,
    welfare: pd.DataFrame,
    psa_results: pd.DataFrame,
    convergence_history: dict = None,
    output_dir: str = "output",
):
    """Step 4: Generate manuscript exhibits."""
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

    plot_outcome_radar(summary, figdir / "exhibit2_outcomes.pdf")
    plot_equity_impact(psa_results, figdir / "exhibit3_equity.pdf")
    plot_welfare_waterfall(welfare, figdir / "exhibit4_welfare.pdf")

    logger.info(f"Figures saved to {figdir}")


def main():
    parser = argparse.ArgumentParser(description="AI ACO Analysis Pipeline")
    parser.add_argument("--debate-only", action="store_true", help="Run only the debate step")
    parser.add_argument("--microsim-only", action="store_true", help="Run only microsimulation")
    parser.add_argument("--n-iterations", type=int, default=1000, help="PSA iterations")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--skip-debate", action="store_true", help="Skip debate, use cached results")
    args = parser.parse_args()

    output_dir = args.output_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    convergence_history = None

    if args.debate_only:
        run_debate(output_dir)
        return

    if not args.skip_debate and not args.microsim_only:
        debate_results = run_debate(output_dir)
        convergence_history = debate_results.get("convergence_history")

    if args.microsim_only or not args.debate_only:
        psa_results, summary = run_microsim(args.n_iterations, output_dir)
        welfare, equity_welfare = run_welfare(summary, psa_results, output_dir)

        try:
            run_visualization(summary, welfare, psa_results, convergence_history, output_dir)
        except ImportError as e:
            logger.warning(f"Visualization skipped (missing dependency): {e}")

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
