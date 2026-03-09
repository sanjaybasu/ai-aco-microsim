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
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional


# WTP threshold for QALYs (standard US, 2024 USD)
WTP_PER_QALY = 100_000

# QALY decrements per acute care event (RECODe-derived)
QALY_DECREMENT_HOSP = 0.05   # per hospitalization
QALY_DECREMENT_ED = 0.01     # per ED visit
QALY_GAIN_PCP = 0.002        # per additional PCP visit (preventive value)


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
