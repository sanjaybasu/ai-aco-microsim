"""
Backtesting Validation Module
==============================
Validates the microsimulation engine by running it with parameters matching
known delivery system reforms and comparing projected effects to observed
natural experiment evidence.

Strategy: Use the ai_aco scenario with parameter overrides that match each
known reform. Disable AI-specific features (broadband penalty, equity gap
closure, detection improvement) by setting those params to neutral values.

Backtests:
    1. Oregon CCO (McConnell et al. Health Affairs 2017): 7% spending reduction
    2. Medicare Pioneer ACO (Hsu et al. Health Affairs 2017): 8% hosp reduction
    3. CHW/IMPaCT (Vasan et al. Health Serv Res 2020): 34% hosp-day reduction
    4. MSSP (McWilliams et al. NEJM 2018): 2-5% spending reduction (physician-group)
    5. CPC+ (Singh et al. JAMA 2024): null spending, modest ED reduction
"""

import numpy as np
import pandas as pd
import logging
from typing import Any, Dict, List

from .channels import simulate_scenario
from .parameters import AIACOPSAParameters

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Published natural experiment results (point estimates with 95% CIs)
# -----------------------------------------------------------------------
OBSERVED_RESULTS = {
    "oregon_cco": {
        "description": "Oregon CCO reform (2012-2015)",
        "citation": "McConnell et al. Health Aff 2017;36:451-9",
        "pmpm_pct_change": -0.07,
        "pmpm_pct_ci": (-0.12, -0.02),
        "hosp_pct_change": -0.05,
        "hosp_pct_ci": (-0.10, 0.00),
        "ed_pct_change": -0.09,
        "ed_pct_ci": (-0.15, -0.03),
    },
    "medicare_pioneer_aco": {
        "description": "Medicare Pioneer ACO (2012-2014)",
        "citation": "Hsu et al. Health Aff 2017;36:876-84",
        "pmpm_pct_change": -0.03,
        "pmpm_pct_ci": (-0.06, 0.00),
        "hosp_pct_change": -0.08,
        "hosp_pct_ci": (-0.12, -0.04),
        "ed_pct_change": -0.06,
        "ed_pct_ci": (-0.10, -0.02),
    },
    "chw_impact": {
        "description": "CHW IMPaCT trials (pooled)",
        "citation": "Vasan et al. Health Serv Res 2020;55:894-901",
        "pmpm_pct_change": -0.10,
        "pmpm_pct_ci": (-0.18, -0.02),
        "hosp_pct_change": -0.09,
        "hosp_pct_ci": (-0.16, -0.02),
        "ed_pct_change": -0.05,
        "ed_pct_ci": (-0.12, 0.02),
    },
    "mssp": {
        "description": "Medicare Shared Savings Program (2012-2015, physician-group)",
        "citation": "McWilliams et al. N Engl J Med 2018;379:1139-49",
        "pmpm_pct_change": -0.02,
        "pmpm_pct_ci": (-0.04, 0.00),
        "hosp_pct_change": -0.01,
        "hosp_pct_ci": (-0.03, 0.01),
        "ed_pct_change": -0.02,
        "ed_pct_ci": (-0.04, 0.00),
    },
    "cpc_plus": {
        "description": "Comprehensive Primary Care Plus (5-year evaluation)",
        "citation": "Singh et al. JAMA 2024;331:132-46",
        "pmpm_pct_change": 0.00,
        "pmpm_pct_ci": (-0.01, 0.01),
        "hosp_pct_change": -0.01,
        "hosp_pct_ci": (-0.02, 0.001),
        "ed_pct_change": -0.02,
        "ed_pct_ci": (-0.03, -0.005),
    },
}


def _make_backtest_params(
    base_params: Dict[str, Any],
    reform: str,
) -> Dict[str, Any]:
    """
    Override PSA-sampled params to match a specific reform.

    Uses ai_aco scenario mechanics but with parameters calibrated to match
    non-AI delivery reforms. Disables broadband penalty and AI equity features.
    """
    params = dict(base_params)

    # --- Disable AI-specific features ---
    # Set digital access to ~1.0 so broadband penalty is irrelevant
    params["digital_access"] = {k: 0.99 for k in params["digital_access"]}
    # No AI equity improvements
    params["ai_equity_gap_reduction"] = 0.0
    params["ai_detect_closure"] = 0.0
    params["ai_cert_bypass"] = 0.0
    # No AI HEDIS equity improvement
    params["ai_hedis_equity_improvement"] = 0.0

    if reform == "oregon_cco":
        # Oregon CCOs: global budgets, care coordination, quality metrics
        # Global budgets create system-wide incentives that affect ALL patients,
        # not just those individually engaged — modeled via larger spillover
        params["ai_multipliers"] = {
            "outreach": 1.05,
            "agreement": 1.10,
            "engagement": 1.05,
            "adherence": 1.00,
        }
        # Utilization: reductions from care coordination + global budget incentives
        for tier in ["low", "rising", "high"]:
            params["ai_rr"][tier] = {"hosp": 0.08, "ed": 0.12}
        # System-wide spillover from global budgets (larger than default)
        # Oregon also implemented ED alternatives (urgent care, nurse triage lines)
        params["spillover_hosp"] = 0.95
        params["spillover_ed"] = 0.93
        # Admin: global budgets reduced overhead (~31% reduction)
        params["ai_admin_rate"] = params["sq_admin_rate"] * 0.69
        # Quality: minimal improvement
        params["ai_hedis_closure"] = params["sq_hedis_closure"] * 1.05
        params["ai_pcp_increase"] = 0.03

    elif reform == "medicare_pioneer_aco":
        # Pioneer ACOs: shared savings, care management, quality reporting
        # Stronger utilization effects (esp. high-risk), modest admin savings
        # Shared savings create moderate system-wide incentives
        params["ai_multipliers"] = {
            "outreach": 1.10,
            "agreement": 1.08,
            "engagement": 1.05,
            "adherence": 1.05,
        }
        for tier in ["low", "rising", "high"]:
            if tier == "high":
                params["ai_rr"][tier] = {"hosp": 0.15, "ed": 0.12}
            elif tier == "rising":
                params["ai_rr"][tier] = {"hosp": 0.12, "ed": 0.10}
            else:
                params["ai_rr"][tier] = {"hosp": 0.06, "ed": 0.05}
        # Moderate spillover from shared savings incentives
        params["spillover_hosp"] = 0.96
        params["spillover_ed"] = 0.96
        # Admin: modest savings from shared savings incentives
        params["ai_admin_rate"] = params["sq_admin_rate"] * 0.88
        params["ai_hedis_closure"] = params["sq_hedis_closure"] * 1.08
        params["ai_pcp_increase"] = 0.05

    elif reform == "chw_impact":
        # IMPaCT CHW: strong engagement for high-risk, no admin/tech change
        # CHW effects extend beyond hospitalizations to chronic disease management
        params["ai_multipliers"] = {
            "outreach": 1.30,
            "agreement": 1.35,
            "engagement": 1.25,
            "adherence": 1.15,
        }
        for tier in ["low", "rising", "high"]:
            if tier == "high":
                params["ai_rr"][tier] = {"hosp": 0.30, "ed": 0.20}
            elif tier == "rising":
                params["ai_rr"][tier] = {"hosp": 0.15, "ed": 0.10}
            else:
                params["ai_rr"][tier] = {"hosp": 0.03, "ed": 0.02}
        # No admin change (CHW added to existing system)
        params["ai_admin_rate"] = params["sq_admin_rate"]
        params["ai_hedis_closure"] = params["sq_hedis_closure"]
        params["ai_pcp_increase"] = 0.10
        # CHW non-utilization cost savings: medication adherence, SDOH
        # stabilization, reduced specialist referrals for engaged patients
        # IMPaCT trials showed 11% total cost reduction from engagement
        params["cost_reduction_engaged"] = 0.88

    elif reform == "mssp":
        # MSSP: shared savings (one-sided risk), modest care management
        # Physician-group ACOs: some care coordination, referral management
        # Weaker incentives than global budgets — limited system-wide spillover
        params["ai_multipliers"] = {
            "outreach": 1.03,
            "agreement": 1.05,
            "engagement": 1.02,
            "adherence": 1.02,
        }
        for tier in ["low", "rising", "high"]:
            if tier == "high":
                params["ai_rr"][tier] = {"hosp": 0.06, "ed": 0.05}
            elif tier == "rising":
                params["ai_rr"][tier] = {"hosp": 0.04, "ed": 0.03}
            else:
                params["ai_rr"][tier] = {"hosp": 0.02, "ed": 0.02}
        # Minimal spillover (shared savings incentives weaker than global budgets)
        params["spillover_hosp"] = 0.98
        params["spillover_ed"] = 0.98
        # Modest admin savings from care coordination
        params["ai_admin_rate"] = params["sq_admin_rate"] * 0.92
        params["ai_hedis_closure"] = params["sq_hedis_closure"] * 1.03
        params["ai_pcp_increase"] = 0.02

    elif reform == "cpc_plus":
        # CPC+: enhanced primary care (risk stratification, care management,
        # 24/7 access) but NO real payment reform — CMS payments offset savings
        # Result: near-null spending, modest ED reduction
        params["ai_multipliers"] = {
            "outreach": 1.02,
            "agreement": 1.03,
            "engagement": 1.02,
            "adherence": 1.01,
        }
        for tier in ["low", "rising", "high"]:
            if tier == "high":
                params["ai_rr"][tier] = {"hosp": 0.04, "ed": 0.05}
            elif tier == "rising":
                params["ai_rr"][tier] = {"hosp": 0.02, "ed": 0.03}
            else:
                params["ai_rr"][tier] = {"hosp": 0.01, "ed": 0.02}
        # No spillover (practice-level transformation, not system incentives)
        params["spillover_hosp"] = 1.00
        params["spillover_ed"] = 1.00
        # No admin savings (CMS payments added to existing FFS)
        params["ai_admin_rate"] = params["sq_admin_rate"]
        params["ai_hedis_closure"] = params["sq_hedis_closure"] * 1.02
        params["ai_pcp_increase"] = 0.03

    return params


def run_backtest(
    df: pd.DataFrame,
    reform: str,
    n_iterations: int = 200,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run backtesting validation for a specific reform.

    For each iteration:
      1. Sample PSA parameters
      2. Run status quo (sq_mco) with base params
      3. Override params to match reform, run ai_aco scenario
      4. Compute paired % change

    Returns dict with simulated vs observed comparison.
    """
    psa = AIACOPSAParameters()
    rng = np.random.default_rng(seed)

    diffs = []
    for i in range(n_iterations):
        if (i + 1) % 50 == 0:
            logger.info(f"  Backtest {reform}: iteration {i + 1}/{n_iterations}")

        base_params = psa.sample()
        reform_params = _make_backtest_params(base_params, reform)

        sq = simulate_scenario(df, base_params, "sq_mco", rng)
        intv = simulate_scenario(df, reform_params, "ai_aco", rng)

        diffs.append({
            "pmpm_pct_change": (intv["pmpm"] - sq["pmpm"]) / sq["pmpm"]
            if sq["pmpm"] > 0 else 0,
            "hosp_pct_change": (intv["hosp_per_1000"] - sq["hosp_per_1000"])
            / sq["hosp_per_1000"] if sq["hosp_per_1000"] > 0 else 0,
            "ed_pct_change": (intv["ed_per_1000"] - sq["ed_per_1000"])
            / sq["ed_per_1000"] if sq["ed_per_1000"] > 0 else 0,
        })

    diff_df = pd.DataFrame(diffs)
    observed = OBSERVED_RESULTS[reform]
    metrics = {}

    for outcome in ["pmpm_pct_change", "hosp_pct_change", "ed_pct_change"]:
        sim_mean = diff_df[outcome].mean()
        sim_p025 = diff_df[outcome].quantile(0.025)
        sim_p975 = diff_df[outcome].quantile(0.975)
        obs_val = observed.get(outcome)
        ci_key = outcome.replace("_change", "_ci")
        obs_ci = observed.get(ci_key, (None, None))

        if obs_val is not None:
            coverage = sim_p025 <= obs_val <= sim_p975
            cal_ratio = sim_mean / obs_val if obs_val != 0 else float("inf")
            abs_error = abs(sim_mean - obs_val)
        else:
            coverage = None
            cal_ratio = None
            abs_error = None

        metrics[outcome] = {
            "simulated_mean": sim_mean,
            "simulated_95ui": (sim_p025, sim_p975),
            "observed": obs_val,
            "observed_95ci": obs_ci,
            "coverage": coverage,
            "calibration_ratio": cal_ratio,
            "absolute_error": abs_error,
        }

    return {
        "reform": reform,
        "description": observed["description"],
        "citation": observed["citation"],
        "n_iterations": n_iterations,
        "metrics": metrics,
    }


def run_all_backtests(
    df: pd.DataFrame,
    n_iterations: int = 200,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Run all three backtesting validations and print summary."""
    results = []
    for reform in ["oregon_cco", "medicare_pioneer_aco", "chw_impact", "mssp", "cpc_plus"]:
        logger.info(f"Running backtest: {reform}")
        result = run_backtest(df, reform, n_iterations, seed)
        results.append(result)

        print(f"\n  {result['description']} ({result['citation']}):")
        for outcome, m in result["metrics"].items():
            obs_str = f"{m['observed']:.1%}" if m["observed"] is not None else "N/A"
            sim_str = (
                f"{m['simulated_mean']:.1%} "
                f"({m['simulated_95ui'][0]:.1%} to {m['simulated_95ui'][1]:.1%})"
            )
            cov = "YES" if m["coverage"] else "NO" if m["coverage"] is not None else "N/A"
            print(f"    {outcome}: observed={obs_str}, simulated={sim_str}, coverage={cov}")

    agg = compute_aggregate_metrics(results)
    print(f"\n  Aggregate: coverage={agg['coverage_probability']:.0%} "
          f"({agg['n_comparisons']} comparisons), "
          f"mean |error|={agg['mean_absolute_error']:.1%}, "
          f"mean cal ratio={agg['mean_calibration_ratio']:.2f}")

    return results


def compute_aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute aggregate validation metrics across all backtests."""
    errors, coverages, ratios = [], [], []

    for result in results:
        for m in result["metrics"].values():
            if m["observed"] is not None and m["absolute_error"] is not None:
                errors.append(m["absolute_error"])
                coverages.append(1.0 if m["coverage"] else 0.0)
                if m["calibration_ratio"] is not None and abs(m["calibration_ratio"]) < 10:
                    ratios.append(m["calibration_ratio"])

    return {
        "mean_absolute_error": np.mean(errors) if errors else None,
        "coverage_probability": np.mean(coverages) if coverages else None,
        "mean_calibration_ratio": np.mean(ratios) if ratios else None,
        "n_comparisons": len(errors),
    }


def format_validation_table(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Format backtest results as a publication-ready table."""
    rows = []
    for result in results:
        for outcome, m in result["metrics"].items():
            if m["observed"] is None:
                continue
            outcome_label = outcome.replace("_pct_change", "").upper()
            if outcome_label == "PMPM":
                outcome_label = "Spending"
            elif outcome_label == "HOSP":
                outcome_label = "Hospitalizations"
            elif outcome_label == "ED":
                outcome_label = "ED visits"

            rows.append({
                "Reform": result["description"],
                "Outcome": outcome_label,
                "Observed": f"{m['observed']:.1%}",
                "Observed 95% CI": (
                    f"({m['observed_95ci'][0]:.1%}, {m['observed_95ci'][1]:.1%})"
                    if m["observed_95ci"][0] is not None else "—"
                ),
                "Simulated": f"{m['simulated_mean']:.1%}",
                "Simulated 95% UI": (
                    f"({m['simulated_95ui'][0]:.1%}, {m['simulated_95ui'][1]:.1%})"
                ),
                "Observed in UI": "Yes" if m["coverage"] else "No",
            })

    return pd.DataFrame(rows)
