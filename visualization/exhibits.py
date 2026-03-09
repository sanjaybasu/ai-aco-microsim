"""
Manuscript Figure Generation (NEJM AI format)
==============================================
Main text (4 figures):
    Figure 1 — Study overview (conceptual, created manually)
    Figure 2 — Multi-agent debate convergence heatmap
    Figure 3 — Calibration and external validation (backtesting)
    Figure 4 — Conditions for improvement (acceptability curve)

Supplement (3 eFigures):
    eFigure 1 — Equity: absolute reduction in outcomes by race
    eFigure 2 — Welfare waterfall decomposition
    eFigure 3 — Multi-dimensional outcome radar chart
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Any, Dict, List, Optional

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

REFORM_LABELS = {
    "oregon_cco": "Oregon CCO",
    "medicare_pioneer_aco": "Pioneer ACO",
    "chw_impact": "CHW/IMPaCT",
    "mssp": "MSSP",
    "cpc_plus": "CPC+",
}

REFORM_COLORS = {
    "oregon_cco": "#1f77b4",
    "medicare_pioneer_aco": "#ff7f0e",
    "chw_impact": "#2ca02c",
    "mssp": "#d62728",
    "cpc_plus": "#9467bd",
}

OUTCOME_LABELS = {
    "pmpm_pct_change": "Spending",
    "hosp_pct_change": "Hospitalizations",
    "ed_pct_change": "ED Visits",
}


# =====================================================================
# MAIN TEXT FIGURES
# =====================================================================

def plot_figure2_convergence(
    convergence_history: Dict[str, List[float]],
    save_path: Optional[Path] = None,
):
    """Figure 2: Convergence heatmap (12 domains x K rounds)."""
    domains = list(convergence_history.keys())
    n_rounds = max(len(v) for v in convergence_history.values())

    matrix = np.full((len(domains), n_rounds), np.nan)
    for i, domain in enumerate(domains):
        vals = convergence_history[domain]
        for j, v in enumerate(vals):
            matrix[i, j] = v

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=0.5)

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
    ax.set_title("Figure 2. Multi-Agent Debate Convergence\n"
                  "(Coefficient of Variation Across 8 Expert Agents)")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Coefficient of Variation")
    cbar.ax.axhline(y=0.15, color="black", linestyle="--", linewidth=1)
    cbar.ax.text(1.5, 0.15, "Threshold", fontsize=7, va="center")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_figure3_validation(
    backtest_results: List[Dict[str, Any]],
    calibration_data: Optional[Dict] = None,
    save_path: Optional[Path] = None,
):
    """
    Figure 3: Calibration and External Validation.
    Left: calibration against benchmarks. Right: backtesting against 5 reforms.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # ----- Panel A: Calibration (if data provided) -----
    if calibration_data:
        metrics = list(calibration_data.keys())
        y_pos = np.arange(len(metrics))
        for i, metric in enumerate(metrics):
            d = calibration_data[metric]
            ax1.errorbar(d["simulated"], i, xerr=[[d["simulated"] - d["sim_lo"]],
                         [d["sim_hi"] - d["simulated"]]],
                         fmt="o", color="#1f77b4", capsize=4, markersize=6)
            ax1.barh(i, d["bench_hi"] - d["bench_lo"], left=d["bench_lo"],
                     height=0.3, color="#cccccc", alpha=0.6, zorder=0)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(metrics)
        ax1.set_xlabel("Value")
        ax1.set_title("Panel A: Calibration vs. Published Benchmarks")
    else:
        ax1.text(0.5, 0.5, "Calibration data\nnot provided",
                 ha="center", va="center", transform=ax1.transAxes, fontsize=12)
        ax1.set_title("Panel A: Calibration vs. Published Benchmarks")

    # ----- Panel B: Backtesting validation -----
    all_comparisons = []
    for result in backtest_results:
        reform = result["reform"]
        for outcome, m in result["metrics"].items():
            if m["observed"] is None:
                continue
            all_comparisons.append({
                "reform": reform,
                "outcome": outcome,
                "label": f"{REFORM_LABELS.get(reform, reform)}\n{OUTCOME_LABELS.get(outcome, outcome)}",
                "observed": m["observed"],
                "obs_lo": m["observed_95ci"][0] if m["observed_95ci"][0] is not None else m["observed"],
                "obs_hi": m["observed_95ci"][1] if m["observed_95ci"][1] is not None else m["observed"],
                "simulated": m["simulated_mean"],
                "sim_lo": m["simulated_95ui"][0],
                "sim_hi": m["simulated_95ui"][1],
                "coverage": m["coverage"],
            })

    n = len(all_comparisons)
    y_positions = np.arange(n)

    for i, comp in enumerate(all_comparisons):
        color = REFORM_COLORS.get(comp["reform"], "#333")

        # Simulated (dot + error bar)
        ax2.errorbar(comp["simulated"], i, xerr=[[comp["simulated"] - comp["sim_lo"]],
                     [comp["sim_hi"] - comp["simulated"]]],
                     fmt="o", color=color, capsize=3, markersize=5, zorder=3)

        # Observed (diamond)
        ax2.plot(comp["observed"], i, "D", color=color, markersize=7,
                 markeredgecolor="black", markeredgewidth=0.5, zorder=4)

        # Observed CI (thin line)
        ax2.plot([comp["obs_lo"], comp["obs_hi"]], [i, i],
                 "-", color=color, alpha=0.3, linewidth=6, zorder=1)

    ax2.set_yticks(y_positions)
    ax2.set_yticklabels([c["label"] for c in all_comparisons], fontsize=7)
    ax2.set_xlabel("Percent Change from Baseline")
    ax2.axvline(x=0, color="black", linewidth=0.5, linestyle="--")
    ax2.set_title("Panel B: Backtesting Against 5 Natural Experiments")

    # Format x-axis as percentages
    from matplotlib.ticker import FuncFormatter
    ax2.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#666",
                    markersize=6, label="Simulated (95% UI)"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#666",
                    markeredgecolor="black", markersize=7, label="Observed (95% CI)"),
    ]
    ax2.legend(handles=legend_elements, loc="lower left", fontsize=7)

    fig.suptitle("Figure 3. Calibration and External Validation", fontsize=11, y=1.01)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_figure4_acceptability(
    psa_results: pd.DataFrame,
    save_path: Optional[Path] = None,
):
    """
    Figure 4: Conditions for Improvement.
    Probability of net savings as a function of AI ACO admin cost rate.
    Analogous to a cost-effectiveness acceptability curve.
    """
    # Extract paired iteration-level differences
    sq = psa_results[psa_results["scenario"] == "sq_mco"].sort_values("iteration")
    ai = psa_results[psa_results["scenario"] == "ai_aco"].sort_values("iteration")

    if sq.empty or ai.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, "PSA data not available", ha="center", va="center",
                transform=ax.transAxes)
        return fig

    sq_pmpm = sq["pmpm"].values
    ai_pmpm = ai["pmpm"].values
    ai_admin = ai["admin_cost_pct"].values

    # For each hypothetical admin rate, compute P(savings > 0)
    admin_rates = np.arange(0.02, 0.11, 0.005)
    probs = []

    for rate in admin_rates:
        # Recompute AI PMPM at this admin rate
        # Original: total_cost = medical / (1 - admin_rate)
        # Approximate: scale PMPM by (1-orig_admin)/(1-new_admin)
        adjusted_pmpm = ai_pmpm * (1 - ai_admin) / (1 - rate)
        savings = sq_pmpm - adjusted_pmpm
        prob_positive = np.mean(savings > 0)
        probs.append(prob_positive)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(admin_rates * 100, probs, "b-", linewidth=2)
    ax.fill_between(admin_rates * 100, probs, alpha=0.1, color="blue")

    # Reference lines
    ax.axhline(y=0.5, color="gray", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.axvline(x=8.3, color="red", linestyle="--", linewidth=1.2, label="MCO baseline (8.3%)")
    ax.axvline(x=3.0, color="green", linestyle="--", linewidth=1.2, label="AI ACO projected (3.0%)")

    # Shade traditional Medicaid admin range
    ax.axvspan(2, 4, alpha=0.1, color="green", label="Traditional Medicaid range")

    ax.set_xlabel("AI ACO Administrative Cost Rate (% of Premium)")
    ax.set_ylabel("Probability of Net Savings vs. Status Quo MCO")
    ax.set_title("Figure 4. Conditions for Improvement:\n"
                 "Probability of Net Savings by Administrative Cost Rate")
    ax.set_xlim(2, 10)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="lower left")

    # Annotate key points
    for target_rate in [3.0, 5.0, 6.0, 7.0, 8.0]:
        idx = np.argmin(np.abs(admin_rates * 100 - target_rate))
        p = probs[idx]
        ax.annotate(f"{p:.0%}", (target_rate, p), textcoords="offset points",
                    xytext=(8, 5), fontsize=7, color="blue")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


# =====================================================================
# SUPPLEMENT FIGURES
# =====================================================================

def plot_efigure1_equity(
    psa_results: pd.DataFrame,
    save_path: Optional[Path] = None,
):
    """
    eFigure 1: Equity — absolute reduction in outcomes by race.
    Panel A: Reduction in hospitalizations per 1,000 PY by race/ethnicity.
    Panel B: Reduction in ED visits per 1,000 PY by race/ethnicity.
    Shows that all groups improve (positive reductions for all).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    races = ["white", "black", "hispanic", "aian"]
    race_labels = {"white": "White", "black": "Black", "hispanic": "Hispanic", "aian": "AIAN"}

    # Compute paired iteration-level reductions by race
    sq = psa_results[psa_results["scenario"] == "sq_mco"].sort_values("iteration")
    ai = psa_results[psa_results["scenario"] == "ai_aco"].sort_values("iteration")

    hosp_reductions = {r: [] for r in races}
    ed_reductions = {r: [] for r in races}

    for (_, sq_row), (_, ai_row) in zip(sq.iterrows(), ai.iterrows()):
        sq_eq = sq_row.get("equity_by_race", {})
        ai_eq = ai_row.get("equity_by_race", {})
        if not isinstance(sq_eq, dict) or not isinstance(ai_eq, dict):
            continue
        for r in races:
            if r in sq_eq and r in ai_eq:
                hosp_reductions[r].append(
                    sq_eq[r].get("hosp_per_1000", 0) - ai_eq[r].get("hosp_per_1000", 0)
                )
                ed_reductions[r].append(
                    sq_eq[r].get("ed_per_1000", 0) - ai_eq[r].get("ed_per_1000", 0)
                )

    # Panel A: Hospitalization reductions
    means_hosp = [np.mean(hosp_reductions[r]) if hosp_reductions[r] else 0 for r in races]
    p025_hosp = [np.percentile(hosp_reductions[r], 2.5) if hosp_reductions[r] else 0 for r in races]
    p975_hosp = [np.percentile(hosp_reductions[r], 97.5) if hosp_reductions[r] else 0 for r in races]

    x = np.arange(len(races))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    bars1 = ax1.bar(x, means_hosp, color=colors, alpha=0.8, width=0.6)
    ax1.errorbar(x, means_hosp,
                 yerr=[np.array(means_hosp) - np.array(p025_hosp),
                       np.array(p975_hosp) - np.array(means_hosp)],
                 fmt="none", color="black", capsize=4)

    ax1.set_xticks(x)
    ax1.set_xticklabels([race_labels[r] for r in races])
    ax1.set_ylabel("Reduction in Hospitalizations\nper 1,000 PY (AI ACO vs. SQ MCO)")
    ax1.set_title("Panel A: Hospitalization Reduction by Race")
    ax1.axhline(y=0, color="black", linewidth=0.5)

    # Panel B: ED reductions
    means_ed = [np.mean(ed_reductions[r]) if ed_reductions[r] else 0 for r in races]
    p025_ed = [np.percentile(ed_reductions[r], 2.5) if ed_reductions[r] else 0 for r in races]
    p975_ed = [np.percentile(ed_reductions[r], 97.5) if ed_reductions[r] else 0 for r in races]

    bars2 = ax2.bar(x, means_ed, color=colors, alpha=0.8, width=0.6)
    ax2.errorbar(x, means_ed,
                 yerr=[np.array(means_ed) - np.array(p025_ed),
                       np.array(p975_ed) - np.array(means_ed)],
                 fmt="none", color="black", capsize=4)

    ax2.set_xticks(x)
    ax2.set_xticklabels([race_labels[r] for r in races])
    ax2.set_ylabel("Reduction in ED Visits\nper 1,000 PY (AI ACO vs. SQ MCO)")
    ax2.set_title("Panel B: ED Visit Reduction by Race")
    ax2.axhline(y=0, color="black", linewidth=0.5)

    fig.suptitle("eFigure 1. Absolute Outcome Improvements by Race/Ethnicity\n"
                 "(AI ACO vs. Status Quo MCO)", fontsize=11, y=1.02)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_efigure2_welfare(
    welfare: pd.DataFrame,
    save_path: Optional[Path] = None,
    scenario: str = "ai_aco",
):
    """eFigure 2: Welfare waterfall decomposition."""
    row = welfare[welfare["scenario"] == scenario]
    if row.empty:
        return None
    row = row.iloc[0]

    components = {
        "Consumer\nSurplus\n(QALYs)": row["consumer_surplus_per_member"],
        "Medical\nSavings": row["medical_savings_per_member_annual"],
        "Admin\nSavings": row["admin_savings_per_member_annual"],
        "Producer\nSurplus": row["producer_surplus_per_member"],
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    labels = list(components.keys())
    values = list(components.values())

    cumulative = 0
    colors = []
    bottoms = []
    for v in values:
        bottoms.append(cumulative if v >= 0 else cumulative + v)
        cumulative += v
        colors.append("#2ca02c" if v >= 0 else "#d62728")

    labels.append("Net Social\nSurplus")
    values.append(cumulative)
    bottoms.append(0)
    colors.append("#1f77b4")

    bars = ax.bar(range(len(labels)), [abs(v) for v in values],
                  bottom=bottoms, color=colors, edgecolor="white", width=0.6)

    for i, (bar, val) in enumerate(zip(bars, values)):
        y_pos = bottoms[i] + abs(val) / 2
        ax.text(i, y_pos, f"${val:,.0f}", ha="center", va="center",
                fontsize=8, fontweight="bold", color="white")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Per Member Per Year (2024 USD)")
    ax.set_title(f"eFigure 2. Social Welfare Decomposition:\n"
                 f"{SCENARIO_LABELS.get(scenario, scenario)} vs. Status Quo MCO")
    ax.axhline(y=0, color="black", linewidth=0.5)

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


def plot_efigure3_radar(
    summary: pd.DataFrame,
    save_path: Optional[Path] = None,
    scenarios: Optional[List[str]] = None,
):
    """eFigure 3: Multi-dimensional outcome radar chart."""
    if scenarios is None:
        scenarios = ["sq_mco", "ai_aco", "enhanced_ffs", "ai_aco_universal"]

    col_ranges = {}
    for col in ["pmpm_mean", "hosp_per_1000_mean", "ed_per_1000_mean",
                 "hedis_gap_closure_mean", "engagement_rate_mean", "admin_cost_pct_mean"]:
        if col in summary.columns:
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
    ax.set_title("eFigure 3. Multi-Dimensional Outcome Comparison",
                  y=1.08, fontsize=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig
