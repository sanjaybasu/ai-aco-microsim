"""
Welfare Analysis for AI ACO Microsimulation
============================================
Hicks-Kaldor social welfare comparison across scenarios with
equity-weighted analysis (Atkinson inequality-aversion parameter).

Total Social Surplus = Consumer Surplus (QALYs) +
                       Government Surplus (program savings) +
                       Producer Surplus (provider revenue change)

Government surplus is decomposed into:
  - Medical savings (utilization reduction)
  - Administrative savings (overhead reduction)
These are NOT additive — both are components of total PMPM savings.

QALY weight sources and rationale:
  - Hospitalization (0.05 per event): Based on condition-weighted average
    QALY decrement for a 3-4 day hospitalization episode in a Medicaid
    population. Consistent with ranges in Briggs et al. (Value Health 2016)
    for ambulatory care-sensitive condition hospitalizations (range 0.02-0.12
    depending on condition mix and duration).
  - ED visit (0.01 per event): Per-visit disutility for ED encounters not
    resulting in hospitalization. Consistent with Jiang et al. (Med Decis
    Making 2017) estimates for acute care visits.
  - PCP visit (0.002 per event): Marginal preventive care value per additional
    visit. Represents QALY value of completed preventive care processes
    (screening, medication reconciliation) rather than the visit itself.
  These values are within published ranges but are not derived from a single
  validated source; results should be interpreted alongside utilization and
  cost findings. QALY sensitivity analysis available via sensitivity_qaly_weights().
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional


# WTP threshold for QALYs (standard US, 2024 USD)
WTP_PER_QALY = 100_000

# QALY decrements per acute care event
# Sources: Briggs et al. Value Health 2016; Jiang et al. Med Decis Making 2017
# Note: condition-weighted estimates for Medicaid adult population mix
# See sensitivity_qaly_weights() for range analysis
QALY_DECREMENT_HOSP = 0.05   # per hospitalization (range tested: 0.02-0.10)
QALY_DECREMENT_ED = 0.01     # per ED visit (range tested: 0.005-0.02)
QALY_GAIN_PCP = 0.002        # per additional PCP visit (range tested: 0.001-0.005)


def compute_welfare(
    psa_summary: pd.DataFrame,
    baseline_scenario: str = "sq_mco",
    wtp_per_qaly: float = WTP_PER_QALY,
) -> pd.DataFrame:
    """
    Compute welfare surplus for each scenario relative to baseline.

    Government surplus = total PMPM savings × 12. This already includes
    both medical savings (utilization) and administrative savings.
    We decompose but do NOT double-count.
    """
    baseline = psa_summary[psa_summary["scenario"] == baseline_scenario].iloc[0]

    welfare_rows = []
    for _, row in psa_summary.iterrows():
        scenario = row["scenario"]

        # ----- Consumer Surplus (QALY gains) -----
        delta_hosp = baseline["hosp_per_1000_mean"] - row["hosp_per_1000_mean"]
        delta_ed = baseline["ed_per_1000_mean"] - row["ed_per_1000_mean"]
        delta_pcp = row["pcp_per_1000_mean"] - baseline["pcp_per_1000_mean"]

        qaly_gain_per_1000 = (
            delta_hosp * QALY_DECREMENT_HOSP
            + delta_ed * QALY_DECREMENT_ED
            + max(delta_pcp, 0) * QALY_GAIN_PCP
        )

        # HEDIS quality improvement (each 1pp gap closure ≈ 0.001 QALY)
        hedis_delta = row["hedis_gap_closure_mean"] - baseline["hedis_gap_closure_mean"]
        qaly_gain_per_1000 += hedis_delta * 1000 * 0.001

        consumer_surplus_per_member = qaly_gain_per_1000 / 1000 * wtp_per_qaly

        # ----- Government Surplus (total Medicaid program savings) -----
        # This is the TOTAL savings — includes both medical and admin components
        pmpm_savings = baseline["pmpm_mean"] - row["pmpm_mean"]
        govt_surplus_per_member_annual = pmpm_savings * 12

        # Decompose government surplus (for reporting, NOT additive)
        admin_delta = baseline["admin_cost_pct_mean"] - row["admin_cost_pct_mean"]
        # Admin savings component: how much of the PMPM reduction is from admin
        admin_savings_per_member_annual = admin_delta * baseline["pmpm_mean"] * 12
        # Medical savings component: remainder
        medical_savings_per_member_annual = govt_surplus_per_member_annual - admin_savings_per_member_annual

        # ----- Producer Surplus (provider net income change) -----
        avg_pcp_margin = 40  # USD per visit
        producer_surplus_per_member = delta_pcp / 1000 * avg_pcp_margin

        # ----- Net Social Surplus per member per year -----
        net_surplus_per_member = (
            consumer_surplus_per_member
            + govt_surplus_per_member_annual
            + producer_surplus_per_member
        )

        # ----- Equity metrics -----
        bw_gap_change = baseline["bw_hosp_gap_mean"] - row["bw_hosp_gap_mean"]
        hedis_equity_change = baseline["hedis_racial_gap_mean"] - row["hedis_racial_gap_mean"]

        welfare_rows.append({
            "scenario": scenario,
            "consumer_surplus_per_member": consumer_surplus_per_member,
            "govt_surplus_per_member_annual": govt_surplus_per_member_annual,
            "medical_savings_per_member_annual": medical_savings_per_member_annual,
            "admin_savings_per_member_annual": admin_savings_per_member_annual,
            "producer_surplus_per_member": producer_surplus_per_member,
            "net_surplus_per_member": net_surplus_per_member,
            "qaly_gain_per_1000": qaly_gain_per_1000,
            "pmpm_savings": pmpm_savings,
            "admin_cost_reduction_pp": admin_delta,
            "bw_hosp_gap_reduction": bw_gap_change,
            "hedis_equity_improvement": hedis_equity_change,
            "hosp_reduction_per_1000": delta_hosp,
            "ed_reduction_per_1000": delta_ed,
            "pcp_increase_per_1000": delta_pcp,
        })

    return pd.DataFrame(welfare_rows)


def compute_equity_weighted_welfare(
    psa_results: pd.DataFrame,
    epsilon: float = 1.0,
) -> pd.DataFrame:
    """
    Compute equity-weighted welfare using Atkinson inequality-aversion.

    The Atkinson index penalizes inequality more heavily as epsilon increases:
    - epsilon = 0: utilitarian (no equity weight)
    - epsilon = 0.5: moderate inequality aversion
    - epsilon = 1.0: log utility (standard in health economics)
    - epsilon = 2.0: strong inequality aversion (Rawlsian-leaning)
    """
    rows = []
    for scenario in psa_results["scenario"].unique():
        sdf = psa_results[psa_results["scenario"] == scenario]

        race_healths = {"white": [], "black": [], "hispanic": [], "aian": []}
        for _, row in sdf.iterrows():
            equity = row.get("equity_by_race", {})
            if not isinstance(equity, dict):
                continue
            for race in race_healths:
                if race in equity:
                    hosp = equity[race].get("hosp_per_1000", 200)
                    health = 1000.0 / max(hosp, 1)
                    race_healths[race].append(health)

        mean_health_by_race = {}
        for race, vals in race_healths.items():
            if vals:
                mean_health_by_race[race] = np.mean(vals)

        if mean_health_by_race:
            healths = list(mean_health_by_race.values())
            mean_h = np.mean(healths)

            if epsilon == 1.0:
                ede = np.exp(np.mean(np.log(np.clip(healths, 1e-6, None))))
            else:
                ede = np.mean([h ** (1 - epsilon) for h in healths]) ** (1 / (1 - epsilon))

            atkinson_index = 1.0 - (ede / mean_h) if mean_h > 0 else 0.0
            equity_weighted_welfare = ede
        else:
            atkinson_index = 0.0
            equity_weighted_welfare = 0.0
            mean_h = 0.0

        rows.append({
            "scenario": scenario,
            "epsilon": epsilon,
            "mean_health": mean_h,
            "equally_distributed_equivalent": equity_weighted_welfare,
            "atkinson_index": atkinson_index,
            "health_by_race": mean_health_by_race,
        })

    return pd.DataFrame(rows)


def sensitivity_wtp(
    psa_summary: pd.DataFrame,
    wtp_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Run welfare analysis across multiple WTP thresholds."""
    if wtp_values is None:
        wtp_values = [50_000, 100_000, 150_000, 200_000]

    results = []
    for wtp in wtp_values:
        welfare = compute_welfare(psa_summary, wtp_per_qaly=wtp)
        welfare["wtp_threshold"] = wtp
        results.append(welfare)

    return pd.concat(results, ignore_index=True)


def sensitivity_qaly_weights(
    psa_summary: pd.DataFrame,
    hosp_values: Optional[List[float]] = None,
    ed_values: Optional[List[float]] = None,
    pcp_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Run welfare analysis across a grid of QALY weight assumptions.

    Tests robustness of consumer surplus and net surplus estimates to
    variation in per-event QALY decrements. Each combination is run
    at the base-case WTP of $100,000/QALY.

    Args:
        psa_summary: Output of summarize_psa().
        hosp_values: QALY decrement per hospitalization (default: 0.02, 0.05, 0.10).
        ed_values: QALY decrement per ED visit (default: 0.005, 0.01, 0.02).
        pcp_values: QALY gain per PCP visit (default: 0.001, 0.002, 0.005).

    Returns:
        DataFrame with columns: hosp_qaly, ed_qaly, pcp_qaly, scenario,
        consumer_surplus_per_member, net_surplus_per_member.
    """
    if hosp_values is None:
        hosp_values = [0.02, 0.05, 0.10]
    if ed_values is None:
        ed_values = [0.005, 0.01, 0.02]
    if pcp_values is None:
        pcp_values = [0.001, 0.002, 0.005]

    results = []
    for h in hosp_values:
        for e in ed_values:
            for p in pcp_values:
                baseline = psa_summary[psa_summary["scenario"] == "sq_mco"].iloc[0]
                for _, row in psa_summary.iterrows():
                    scenario = row["scenario"]
                    delta_hosp = baseline["hosp_per_1000_mean"] - row["hosp_per_1000_mean"]
                    delta_ed = baseline["ed_per_1000_mean"] - row["ed_per_1000_mean"]
                    delta_pcp = row["pcp_per_1000_mean"] - baseline["pcp_per_1000_mean"]
                    hedis_delta = row["hedis_gap_closure_mean"] - baseline["hedis_gap_closure_mean"]
                    qaly_gain = (
                        delta_hosp * h
                        + delta_ed * e
                        + max(delta_pcp, 0) * p
                        + hedis_delta * 1000 * 0.001
                    )
                    cs = qaly_gain / 1000 * WTP_PER_QALY
                    pmpm_savings = baseline["pmpm_mean"] - row["pmpm_mean"]
                    net = cs + pmpm_savings * 12
                    results.append({
                        "hosp_qaly": h,
                        "ed_qaly": e,
                        "pcp_qaly": p,
                        "scenario": scenario,
                        "consumer_surplus_per_member": round(cs, 2),
                        "net_surplus_per_member": round(net, 2),
                    })

    return pd.DataFrame(results)


def sensitivity_epsilon(
    psa_results: pd.DataFrame,
    epsilon_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Run equity-weighted welfare across Atkinson inequality-aversion values.

    Args:
        psa_results: Full PSA iteration results from run_psa().
        epsilon_values: Aversion parameters (default: 0.5, 1.0, 2.0).

    Returns:
        DataFrame with columns: epsilon, scenario, equally_distributed_equivalent,
        atkinson_index, mean_health.
    """
    if epsilon_values is None:
        epsilon_values = [0.5, 1.0, 2.0]

    results = []
    for eps in epsilon_values:
        ew = compute_equity_weighted_welfare(psa_results, epsilon=eps)
        results.append(ew)

    return pd.concat(results, ignore_index=True)


def mc_standard_error(psa_results: pd.DataFrame, outcome_col: str, scenario: str) -> Dict[str, float]:
    """
    Compute Monte Carlo standard error for a PSA outcome.

    For 1,000 iterations, the MC standard error is SD / sqrt(N).
    Per CHEERS 2022 item 20, this should be reported alongside
    uncertainty intervals.

    Args:
        psa_results: Full PSA iteration results.
        outcome_col: Column name for the outcome of interest.
        scenario: Scenario name.

    Returns:
        Dict with keys: mean, sd, se_mc, n, ci_95_lower, ci_95_upper.
    """
    sdf = psa_results[psa_results["scenario"] == scenario][outcome_col].dropna()
    n = len(sdf)
    mean = float(sdf.mean())
    sd = float(sdf.std())
    se = sd / np.sqrt(n) if n > 0 else 0.0
    return {
        "scenario": scenario,
        "outcome": outcome_col,
        "n_iterations": n,
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "se_mc": round(se, 4),
        "ci_95_lower": round(float(sdf.quantile(0.025)), 4),
        "ci_95_upper": round(float(sdf.quantile(0.975)), 4),
    }
