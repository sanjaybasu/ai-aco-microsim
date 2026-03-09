"""
5-Channel AI ACO Microsimulation Engine
========================================
Extends the 3-channel Monte Carlo engine from the frailty bias analysis
(algorithm_audit.py::run_monte_carlo) to model AI ACO vs status quo MCO.

Channels:
    1. Access/Eligibility — digital access, language, clinical needs
    2. Engagement Cascade — outreach → agreement → engagement → adherence
    3. Utilization & Cost — risk-stratified hospitalization/ED/PCP + PMPM
    4. Quality — HEDIS gap closure rates
    5. Equity — detection/documentation probability by race × metro

Population: ACS PUMS Medicaid adults (public data, fully replicable).
"""

import numpy as np
import pandas as pd
import logging
from typing import Any, Dict, List, Optional, Tuple

from .parameters import AIACOPSAParameters, STATE_PARAMS

logger = logging.getLogger(__name__)

# Detection/certification base rates (from frailty bias analysis, public literature)
P_DETECT_BASE = {
    "white": 0.72, "black": 0.58, "hispanic": 0.61,
    "asian": 0.69, "aian": 0.52, "other": 0.64,
}
P_CERT_BASE = {
    "white": 0.81, "black": 0.64, "hispanic": 0.67,
    "asian": 0.76, "aian": 0.55, "other": 0.70,
}
RURAL_DETECT_PENALTY = -0.08
RURAL_CERT_PENALTY = -0.06


def assign_risk_tier(n: int, risk_dist: Dict[str, float], rng: np.random.Generator) -> np.ndarray:
    """Assign risk tiers to individuals."""
    return rng.choice(
        ["low", "rising", "high"],
        size=n,
        p=[risk_dist["low"], risk_dist["rising"], risk_dist["high"]],
    )


def simulate_scenario(
    df: pd.DataFrame,
    params: Dict[str, Any],
    scenario: str,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    """
    Simulate one iteration for a given scenario.

    Args:
        df: ACS PUMS population DataFrame with columns:
            race_eth, metro_status, PWGTP (person weight),
            disability domains (DPHY_bin, etc.)
        params: Sampled parameter dict from AIACOPSAParameters.sample()
        scenario: One of "sq_mco", "ai_aco", "enhanced_ffs", "ai_aco_universal"
        rng: NumPy random generator for reproducibility

    Returns:
        Dict with per-scenario outcome metrics.
    """
    n = len(df)
    weights = df["PWGTP"].values.astype(float)
    total_weight = weights.sum()
    races = df["race_eth"].values
    metros = df["metro_status"].values

    # Assign risk tiers
    risk_tiers = assign_risk_tier(n, params["risk_dist"], rng)

    # ===================================================================
    # Channel 1: Access / Eligibility (vectorized)
    # ===================================================================
    # Build race_metro keys and vectorized lookup
    race_metro_keys = np.char.add(np.char.add(races.astype(str), "_"), metros.astype(str))
    p_access_arr = np.full(n, 0.75)
    for key, p_val in params["digital_access"].items():
        p_access_arr[race_metro_keys == key] = p_val
    has_digital_access = rng.random(n) < p_access_arr

    # For AI ACO scenarios, digital access affects engagement
    # For SQ MCO, digital access is less relevant (phone-based)

    # ===================================================================
    # Channel 2: Engagement Cascade
    # ===================================================================
    engaged = np.zeros(n, dtype=bool)
    for tier in ["low", "rising", "high"]:
        mask = risk_tiers == tier
        if not mask.any():
            continue
        n_tier = mask.sum()

        if scenario in ("sq_mco", "admin_only"):
            # admin_only: SQ clinical parameters, AI admin rate
            p_out = params["sq_cascade"][tier]["outreach"]
            p_agr = params["sq_cascade"][tier]["agreement"]
            p_eng = params["sq_cascade"][tier]["engagement"]
            p_adh = params["sq_cascade"][tier]["adherence"]
        elif scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal"):
            p_out = min(0.98, params["sq_cascade"][tier]["outreach"] * params["ai_multipliers"]["outreach"])
            p_agr = min(0.95, params["sq_cascade"][tier]["agreement"] * params["ai_multipliers"]["agreement"])
            p_eng = min(0.95, params["sq_cascade"][tier]["engagement"] * params["ai_multipliers"]["engagement"])
            p_adh = min(0.90, params["sq_cascade"][tier]["adherence"] * params["ai_multipliers"]["adherence"])

            # For AI ACO, no digital access → fallback to SQ cascade rates
            # (phone-only pathway)
            tier_has_digital = has_digital_access[mask]
        elif scenario == "enhanced_ffs":
            # Enhanced FFS: modest improvement over SQ
            p_out = min(0.95, params["sq_cascade"][tier]["outreach"] * 1.05)
            p_agr = min(0.80, params["sq_cascade"][tier]["agreement"] * 1.10)
            p_eng = params["sq_cascade"][tier]["engagement"]
            p_adh = params["sq_cascade"][tier]["adherence"]
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        # Apply racial engagement penalty (vectorized)
        tier_races = races[mask]
        penalties = np.array([params["engagement_racial_penalties"].get(r, 0.0) for r in tier_races])
        if scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_universal"):
            penalties *= (1.0 - params["ai_equity_gap_reduction"])
        overall_p_arr = p_out * p_agr * p_eng * p_adh * (1.0 - penalties)

        # Digital access modifier for AI ACO
        if scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal"):
            no_digital = ~has_digital_access[mask]
            overall_p_arr[no_digital] *= 0.7

        engaged[mask] = rng.random(n_tier) < overall_p_arr

    # ===================================================================
    # Channel 3: Utilization & Cost
    # ===================================================================
    hosp_events = np.zeros(n)
    ed_events = np.zeros(n)
    pcp_events = np.zeros(n)

    for tier in ["low", "rising", "high"]:
        mask = risk_tiers == tier
        if not mask.any():
            continue
        n_tier = mask.sum()
        tier_engaged = engaged[mask]

        base_hosp = params["baseline_util"][tier]["hosp"] / 1000  # convert to probability
        base_ed = params["baseline_util"][tier]["ed"] / 1000
        base_pcp = params["baseline_util"][tier]["pcp"] / 1000

        if scenario in ("sq_mco", "admin_only"):
            hosp_rate = base_hosp
            ed_rate = base_ed
            pcp_rate = base_pcp
        elif scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal"):
            rr_hosp = params["ai_rr"][tier]["hosp"]
            rr_ed = params["ai_rr"][tier]["ed"]
            pcp_mult = 1.0 + params["ai_pcp_increase"]

            if scenario == "ai_aco_optimistic":
                rr_hosp *= 1.3  # upper bound
                rr_ed *= 1.3
            elif scenario == "ai_aco_pessimistic":
                rr_hosp *= 0.5  # lower bound
                rr_ed *= 0.5

            # Engaged patients get intervention effect
            hosp_engaged = base_hosp * (1.0 - rr_hosp)
            ed_engaged = base_ed * (1.0 - rr_ed)
            pcp_engaged = base_pcp * pcp_mult

            # Non-engaged: baseline with spillover (parameterizable for backtesting)
            spillover_hosp = params.get("spillover_hosp", 0.97)
            spillover_ed = params.get("spillover_ed", 0.98)
            hosp_not_engaged = base_hosp * spillover_hosp
            ed_not_engaged = base_ed * spillover_ed

            # Combine
            hosp_rate_arr = np.where(tier_engaged, hosp_engaged, hosp_not_engaged)
            ed_rate_arr = np.where(tier_engaged, ed_engaged, ed_not_engaged)
            pcp_rate_arr = np.where(tier_engaged, pcp_engaged, base_pcp)
        elif scenario == "enhanced_ffs":
            hosp_rate = base_hosp * 0.95
            ed_rate = base_ed * 0.97
            pcp_rate = base_pcp * 1.05

        # Generate events (Poisson)
        if scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal"):
            hosp_events[mask] = rng.poisson(np.clip(hosp_rate_arr, 0, 2), n_tier)
            ed_events[mask] = rng.poisson(np.clip(ed_rate_arr, 0, 5), n_tier)
            pcp_events[mask] = rng.poisson(np.clip(pcp_rate_arr, 0, 15), n_tier)
        else:
            hosp_events[mask] = rng.poisson(np.clip(hosp_rate, 0, 2), n_tier)
            ed_events[mask] = rng.poisson(np.clip(ed_rate, 0, 5), n_tier)
            pcp_events[mask] = rng.poisson(np.clip(pcp_rate, 0, 15), n_tier)

    # Costs
    total_medical_cost = (
        hosp_events * params["costs"]["hosp"]
        + ed_events * params["costs"]["ed"]
        + pcp_events * params["costs"]["pcp"]
        + params["costs"]["pharmacy_pmpm"] * 12  # annual
    )

    # Direct cost reduction for engaged patients (non-utilization savings:
    # medication adherence, SDOH stabilization, reduced specialist referrals)
    cost_reduction_engaged = params.get("cost_reduction_engaged", 1.0)
    if cost_reduction_engaged < 1.0:
        total_medical_cost = np.where(
            engaged, total_medical_cost * cost_reduction_engaged, total_medical_cost
        )

    # Admin costs
    if scenario == "sq_mco":
        admin_rate = params["sq_admin_rate"]
    elif scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal", "admin_only"):
        admin_rate = params["ai_admin_rate"]
    elif scenario == "enhanced_ffs":
        admin_rate = params["sq_admin_rate"] * 0.7  # some improvement
    total_cost = total_medical_cost / (1.0 - admin_rate)

    # ===================================================================
    # Channel 4: Quality (HEDIS)
    # ===================================================================
    if scenario in ("sq_mco", "admin_only"):
        hedis_closure = params["sq_hedis_closure"]
    elif scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_universal"):
        hedis_closure = params["ai_hedis_closure"]
    elif scenario == "ai_aco_pessimistic":
        hedis_closure = (params["sq_hedis_closure"] + params["ai_hedis_closure"]) / 2
    elif scenario == "enhanced_ffs":
        hedis_closure = params["sq_hedis_closure"] * 1.05

    # Racial differential in HEDIS
    hedis_racial_gap = params["hedis_racial_gap"]
    if scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_universal"):
        hedis_racial_gap *= (1.0 - params["ai_hedis_equity_improvement"])

    # ===================================================================
    # Channel 5: Equity (Detection/Documentation) — vectorized
    # ===================================================================
    p_det_arr = np.full(n, 0.64)
    p_cert_arr = np.full(n, 0.70)
    for race_val, p_d in P_DETECT_BASE.items():
        race_mask = races == race_val
        p_det_arr[race_mask] = p_d
    for race_val, p_c in P_CERT_BASE.items():
        race_mask = races == race_val
        p_cert_arr[race_mask] = p_c

    rural_mask = metros == "nonmetro"
    p_det_arr[rural_mask] += RURAL_DETECT_PENALTY
    p_cert_arr[rural_mask] += RURAL_CERT_PENALTY

    # Add noise
    p_det_arr += rng.normal(0, params.get("p_detect_sd", 0.06) * 0.5, n)
    p_cert_arr += rng.normal(0, params.get("p_cert_sd", 0.05) * 0.5, n)

    if scenario in ("ai_aco", "ai_aco_optimistic", "ai_aco_universal"):
        gap_to_ceiling = 0.98 - p_det_arr
        p_det_arr += gap_to_ceiling * params["ai_detect_closure"]
        p_cert_arr = p_cert_arr + (1.0 - p_cert_arr) * params["ai_cert_bypass"]
    elif scenario == "ai_aco_pessimistic":
        gap_to_ceiling = 0.98 - p_det_arr
        p_det_arr += gap_to_ceiling * params["ai_detect_closure"] * 0.5

    p_det_arr = np.clip(p_det_arr, 0.0, 1.0)
    p_cert_arr = np.clip(p_cert_arr, 0.0, 1.0)

    detected = rng.random(n) < p_det_arr
    certified = rng.random(n) < p_cert_arr

    # ===================================================================
    # Aggregate outcomes (population-weighted)
    # ===================================================================
    w = weights / total_weight

    # Per-1000 PY rates (weighted)
    hosp_per_1000 = float(np.sum(hosp_events * w) * 1000)
    ed_per_1000 = float(np.sum(ed_events * w) * 1000)
    pcp_per_1000 = float(np.sum(pcp_events * w) * 1000)

    # PMPM (weighted average)
    pmpm = float(np.sum(total_cost * w / 12))

    # Engagement rate
    engagement_rate = float(np.sum(engaged.astype(float) * w))

    # Quality
    hedis_score = hedis_closure

    # Admin rate
    admin_cost_pct = admin_rate

    # Equity: detection/cert rates by race
    equity_by_race = {}
    for race in ["white", "black", "hispanic", "aian"]:
        race_mask = races == race
        if race_mask.sum() == 0:
            continue
        race_w = weights[race_mask] / weights[race_mask].sum()
        equity_by_race[race] = {
            "detection_rate": float(np.sum(detected[race_mask].astype(float) * race_w)),
            "certification_rate": float(np.sum(certified[race_mask].astype(float) * race_w)),
            "engagement_rate": float(np.sum(engaged[race_mask].astype(float) * race_w)),
            "hosp_per_1000": float(np.sum(hosp_events[race_mask] * race_w) * 1000),
            "ed_per_1000": float(np.sum(ed_events[race_mask] * race_w) * 1000),
        }

    # Racial disparity index (B-W gap in hospitalization)
    bw_hosp_gap = abs(
        equity_by_race.get("black", {}).get("hosp_per_1000", 0)
        - equity_by_race.get("white", {}).get("hosp_per_1000", 0)
    )

    return {
        "scenario": scenario,
        "hosp_per_1000": hosp_per_1000,
        "ed_per_1000": ed_per_1000,
        "pcp_per_1000": pcp_per_1000,
        "pmpm": pmpm,
        "engagement_rate": engagement_rate,
        "hedis_gap_closure": hedis_score,
        "hedis_racial_gap": hedis_racial_gap,
        "admin_cost_pct": admin_cost_pct,
        "equity_by_race": equity_by_race,
        "bw_hosp_gap": bw_hosp_gap,
        "detection_rate_overall": float(np.sum(detected.astype(float) * w)),
        "certification_rate_overall": float(np.sum(certified.astype(float) * w)),
    }


def run_psa(
    df: pd.DataFrame,
    n_iterations: int = 1000,
    scenarios: Optional[List[str]] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run probabilistic sensitivity analysis across all scenarios.

    Args:
        df: ACS PUMS population DataFrame
        n_iterations: Number of PSA iterations
        scenarios: List of scenarios to simulate
        seed: Random seed

    Returns:
        DataFrame with one row per (iteration, scenario) combination.
    """
    if scenarios is None:
        scenarios = ["sq_mco", "ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic",
                      "enhanced_ffs", "ai_aco_universal"]

    psa_params = AIACOPSAParameters()
    rng = np.random.default_rng(seed)
    results = []

    import time as _time
    _t0 = _time.time()

    for i in range(n_iterations):
        if (i + 1) % 10 == 0:
            elapsed = _time.time() - _t0
            rate = (i + 1) / elapsed
            eta = (n_iterations - i - 1) / rate if rate > 0 else 0
            logger.info(f"PSA iteration {i + 1}/{n_iterations} ({rate:.1f} iter/s, ETA {eta:.0f}s)")

        params = psa_params.sample()

        for scenario in scenarios:
            result = simulate_scenario(df, params, scenario, rng)
            result["iteration"] = i
            results.append(result)

    return pd.DataFrame(results)


def summarize_psa(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize PSA results: mean, median, 2.5th/97.5th percentiles.
    """
    outcome_cols = [
        "hosp_per_1000", "ed_per_1000", "pcp_per_1000", "pmpm",
        "engagement_rate", "hedis_gap_closure", "hedis_racial_gap",
        "admin_cost_pct", "bw_hosp_gap", "detection_rate_overall",
        "certification_rate_overall",
    ]

    summary_rows = []
    for scenario in results_df["scenario"].unique():
        sdf = results_df[results_df["scenario"] == scenario]
        row = {"scenario": scenario}
        for col in outcome_cols:
            if col not in sdf.columns:
                continue
            vals = sdf[col].dropna()
            row[f"{col}_mean"] = vals.mean()
            row[f"{col}_median"] = vals.median()
            row[f"{col}_p025"] = vals.quantile(0.025)
            row[f"{col}_p975"] = vals.quantile(0.975)
        summary_rows.append(row)

    return pd.DataFrame(summary_rows)
