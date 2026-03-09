"""
Manuscript Figure Generation (NEJM AI format)
==============================================
4 figures for NEJM AI:
    1. Convergence heatmap (12 domains × K rounds)
    2. Outcome radar/spider chart by scenario
    3. Equity impact (racial and rural-urban gaps)
    4. Welfare waterfall (surplus decomposition)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Dict, List, Optional

# Style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "figure.dpi": 300,
})

SCENARIO_LABELS = {
    "sq_mco": "Status Quo MCO",
    "ai_aco": "AI ACO (Consensus)",
    "ai_aco_optimistic": "AI ACO (Optimistic)",
    "ai_aco_pessimistic": "AI ACO (Pessimistic)",
    "enhanced_ffs": "Enhanced FFS",
    "ai_aco_universal": "AI ACO + Universal",
    "admin_only": "Admin Reform Only",
}

SCENARIO_COLORS = {
    "sq_mco": "#666666",
    "ai_aco": "#1f77b4",
    "ai_aco_optimistic": "#2ca02c",
    "ai_aco_pessimistic": "#d62728",
    "enhanced_ffs": "#ff7f0e",
    "ai_aco_universal": "#9467bd",
    "admin_only": "#8c564b",
}

DOMAIN_LABELS = {
    "clinical_model": "Clinical Model",
    "payment_structure": "Payment",
    "provider_rates": "Provider Rates",
    "org_structure": "Organization",
    "regulatory_pathway": "Regulatory",
    "quality_framework": "Quality",
    "ai_architecture": "AI Architecture",
    "human_oversight": "Human Oversight",
    "sdoh_integration": "SDOH",
    "rural_urban": "Rural/Urban",
    "anti_monopoly": "Anti-Monopoly",
    "ethical_governance": "Ethics/Governance",
}


def plot_convergence_heatmap(
    convergence_history: Dict[str, List[float]],
    save_path: Optional[Path] = None,
):
    """
    Exhibit 1: Convergence heatmap (12 domains × K rounds).
    Shows coefficient of variation decreasing across debate rounds.
    """
    domains = list(convergence_history.keys())
    n_rounds = max(len(v) for v in convergence_history.values())

    # Build matrix
    matrix = np.full((len(domains), n_rounds), np.nan)
    for i, domain in enumerate(domains):
        vals = convergence_history[domain]
        for j, v in enumerate(vals):
            matrix[i, j] = v

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=0.5)

    # Add convergence threshold line annotation
    for i in range(len(domains)):
        for j in range(n_rounds):
            val = matrix[i, j]
            if not np.isnan(val):
                color = "white" if val > 0.3 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, color=color)

    ax.set_xticks(range(n_rounds))
    ax.set_xticklabels([f"Round {i}" for i in range(n_rounds)])
    ax.set_yticks(range(len(domains)))
    ax.set_yticklabels([DOMAIN_LABELS.get(d, d) for d in domains])

    ax.set_xlabel("Debate Round")
    ax.set_title("Figure 1. Multi-Agent Debate Convergence\n"
                  "(Coefficient of Variation Across 8 Expert Agents)")

    # Add convergence threshold line
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Coefficient of Variation")
    cbar.ax.axhline(y=0.15, color="black", linestyle="--", linewidth=1)
    cbar.ax.text(1.5, 0.15, "Threshold", fontsize=7, va="center")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_outcome_radar(
    summary: pd.DataFrame,
    save_path: Optional[Path] = None,
    scenarios: Optional[List[str]] = None,
):
    """
    Exhibit 2: Outcome radar/spider chart comparing scenarios.
    Axes: Cost (PMPM), Hospitalizations, ED visits, Quality (HEDIS),
          Engagement, Admin Efficiency.
    """
    if scenarios is None:
        scenarios = ["sq_mco", "ai_aco", "enhanced_ffs", "ai_aco_universal"]

    # Normalize metrics to 0-1 scale using min-max across scenarios (higher = better)
    col_ranges = {}
    for col in ["pmpm_mean", "hosp_per_1000_mean", "ed_per_1000_mean",
                 "hedis_gap_closure_mean", "engagement_rate_mean", "admin_cost_pct_mean"]:
        col_ranges[col] = (summary[col].min(), summary[col].max())

    def _norm(val, lo, hi, invert=False):
        if hi == lo:
            return 0.5
        n = (val - lo) / (hi - lo)
        return (1 - n) if invert else n

    metrics = {
        "Cost\nEfficiency": lambda r: _norm(r["pmpm_mean"], *col_ranges["pmpm_mean"], invert=True),
        "Hosp.\nReduction": lambda r: _norm(r["hosp_per_1000_mean"], *col_ranges["hosp_per_1000_mean"], invert=True),
        "ED\nReduction": lambda r: _norm(r["ed_per_1000_mean"], *col_ranges["ed_per_1000_mean"], invert=True),
        "Quality\n(HEDIS)": lambda r: _norm(r["hedis_gap_closure_mean"], *col_ranges["hedis_gap_closure_mean"]),
        "Engagement": lambda r: _norm(r["engagement_rate_mean"], *col_ranges["engagement_rate_mean"]),
        "Admin\nEfficiency": lambda r: _norm(r["admin_cost_pct_mean"], *col_ranges["admin_cost_pct_mean"], invert=True),
    }

    labels = list(metrics.keys())
    n_metrics = len(labels)
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for scenario in scenarios:
        row = summary[summary["scenario"] == scenario]
        if row.empty:
            continue
        row = row.iloc[0]
        values = [metrics[m](row) for m in labels]
        values += values[:1]

        color = SCENARIO_COLORS.get(scenario, "#333333")
        label = SCENARIO_LABELS.get(scenario, scenario)
        ax.plot(angles, values, "o-", linewidth=1.5, label=label, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Figure 2. AI ACO vs. Status Quo: Multi-Dimensional Outcome Comparison",
                  y=1.08, fontsize=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_equity_impact(
    psa_results: pd.DataFrame,
    save_path: Optional[Path] = None,
):
    """
    Exhibit 3: Equity impact — racial gaps in key outcomes.
    Two panels: (A) hospitalization rate by race, (B) racial gap change.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    scenarios_to_plot = ["sq_mco", "ai_aco"]
    races = ["white", "black", "hispanic", "aian"]
    race_labels = {"white": "White", "black": "Black", "hispanic": "Hispanic", "aian": "AIAN"}

    # Panel A: Hospitalization rate by race × scenario
    bar_data = {}
    for scenario in scenarios_to_plot:
        sdf = psa_results[psa_results["scenario"] == scenario]
        race_hosp = {r: [] for r in races}
        for _, row in sdf.iterrows():
            equity = row.get("equity_by_race", {})
            if not isinstance(equity, dict):
                continue
            for r in races:
                if r in equity:
                    race_hosp[r].append(equity[r].get("hosp_per_1000", np.nan))
        bar_data[scenario] = {r: np.nanmean(race_hosp[r]) if race_hosp[r] else 0 for r in races}

    x = np.arange(len(races))
    width = 0.35

    for i, scenario in enumerate(scenarios_to_plot):
        vals = [bar_data[scenario].get(r, 0) for r in races]
        color = SCENARIO_COLORS.get(scenario, "#333")
        label = SCENARIO_LABELS.get(scenario, scenario)
        ax1.bar(x + i * width, vals, width, label=label, color=color, alpha=0.8)

    ax1.set_xticks(x + width / 2)
    ax1.set_xticklabels([race_labels[r] for r in races])
    ax1.set_ylabel("Hospitalizations per 1,000 PY")
    ax1.set_title("Panel A: Hospitalization Rate by Race")
    ax1.legend(fontsize=8)

    # Panel B: Racial gap (B-W, H-W, AIAN-W)
    gap_labels = ["Black-White", "Hispanic-White", "AIAN-White"]
    gap_races = ["black", "hispanic", "aian"]

    for i, scenario in enumerate(scenarios_to_plot):
        gaps = []
        for r in gap_races:
            gap = bar_data[scenario].get(r, 0) - bar_data[scenario].get("white", 0)
            gaps.append(gap)
        color = SCENARIO_COLORS.get(scenario, "#333")
        label = SCENARIO_LABELS.get(scenario, scenario)
        ax2.bar(np.arange(len(gap_labels)) + i * width, gaps, width,
                label=label, color=color, alpha=0.8)

    ax2.set_xticks(np.arange(len(gap_labels)) + width / 2)
    ax2.set_xticklabels(gap_labels)
    ax2.set_ylabel("Excess Hospitalizations per 1,000 PY\n(vs White)")
    ax2.set_title("Panel B: Racial Disparity Gap")
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.legend(fontsize=8)

    fig.suptitle("Figure 3. Health Equity Impact of AI ACO vs. Status Quo MCO",
                 fontsize=11, y=1.02)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_welfare_waterfall(
    welfare: pd.DataFrame,
    save_path: Optional[Path] = None,
    scenario: str = "ai_aco",
):
    """
    Exhibit 4: Welfare waterfall chart.
    Decomposes net social surplus into components.
    """
    row = welfare[welfare["scenario"] == scenario]
    if row.empty:
        return None
    row = row.iloc[0]

    # Components (per member per year)
    # Government surplus is decomposed into medical + admin (not additive)
    components = {
        "Consumer\nSurplus\n(QALYs)": row["consumer_surplus_per_member"],
        "Medical\nSavings": row["medical_savings_per_member_annual"],
        "Admin\nSavings": row["admin_savings_per_member_annual"],
        "Producer\nSurplus": row["producer_surplus_per_member"],
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    labels = list(components.keys())
    values = list(components.values())

    # Waterfall
    cumulative = 0
    colors = []
    bottoms = []
    for v in values:
        bottoms.append(cumulative if v >= 0 else cumulative + v)
        cumulative += v
        colors.append("#2ca02c" if v >= 0 else "#d62728")

    # Add total bar
    labels.append("Net Social\nSurplus")
    values.append(cumulative)
    bottoms.append(0)
    colors.append("#1f77b4")

    bars = ax.bar(range(len(labels)), [abs(v) for v in values],
                  bottom=bottoms, color=colors, edgecolor="white", width=0.6)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        y_pos = bottoms[i] + abs(val) / 2
        ax.text(i, y_pos, f"${val:,.0f}", ha="center", va="center",
                fontsize=8, fontweight="bold", color="white")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Per Member Per Year (2024 USD)")
    ax.set_title(f"Figure 4. Social Welfare Decomposition: "
                 f"{SCENARIO_LABELS.get(scenario, scenario)} vs. Status Quo MCO")
    ax.axhline(y=0, color="black", linewidth=0.5)

    # Legend
    patches = [
        mpatches.Patch(color="#2ca02c", label="Gain"),
        mpatches.Patch(color="#d62728", label="Loss"),
        mpatches.Patch(color="#1f77b4", label="Net"),
    ]
    ax.legend(handles=patches, loc="upper left", fontsize=8)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig
