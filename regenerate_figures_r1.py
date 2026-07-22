#!/usr/bin/env python3
"""
Regenerate manuscript figures for revision 1 (BMC HSR).

Fixes the reviewer-noted figure problems:
  * In-image titles now match the BMC manuscript numbering (Reviewer 2 M8):
    Figure 2, Figure 3, eFigure 1-4 (previously mislabeled Figure 3/Figure 4/Figure S1..).
  * Figure 3 y-axis is the probability of net savings, values read from the
    canonical admin sweep, baseline reference line at 7.7% (Reviewer 2 M7).
  * eFigure 4 radar: status-quo MCO drawn with a visible line + fill (Reviewer 2 M12).

Figures read numbers from output/revision1/canonical_results.json at render time;
only the fixed validation/convergence inputs (not affected by the admin re-anchoring)
are embedded as literals, with sources noted.
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CANON = json.load(open(ROOT / "output" / "revision1" / "canonical_results.json"))
FIGDIR = ROOT / "output" / "revision1" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12,
                     "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 10})

# ---- fixed validation inputs (eTable 7/8; not affected by admin re-anchoring) ----
BENCH = {  # published benchmark ranges (Fig 2 panel A)
    "PMPM ($)": (450, 550), "Hosp/1,000 PY": (150, 220), "ED/1,000 PY": (550, 850),
    "HEDIS gap closure (%)": (30, 45), "Admin (% premium)": (5.5, 10.1),
}
BACKTEST = [  # (reform, outcome, observed, obs_lo, obs_hi, sim, sim_lo, sim_hi)
    ("Oregon CCO", "Spending", -7.0, -12, -2, -5.4, -7.8, -3.6),
    ("Oregon CCO", "Hosp", -5.0, -10, 0, -5.6, -8.8, -2.0),
    ("Oregon CCO", "ED", -9.0, -15, -3, -8.0, -9.5, -5.9),
    ("Pioneer ACO", "Spending", -3.0, -6, 0, -3.6, -5.1, -2.2),
    ("Pioneer ACO", "Hosp", -8.0, -12, -4, -5.9, -9.2, -2.9),
    ("Pioneer ACO", "ED", -6.0, -10, -2, -5.1, -6.9, -3.1),
    ("CHW/IMPaCT", "Spending", -10.0, -18, -2, -8.3, -10.5, -6.4),
    ("CHW/IMPaCT", "Hosp", -9.0, -16, -2, -10.1, -13.6, -6.8),
    ("CHW/IMPaCT", "ED", -5.0, -12, 2, -6.0, -7.9, -3.8),
    ("MSSP", "Spending", -2.0, -4, 0, -1.8, -3.1, -0.3),
    ("MSSP", "Hosp", -1.0, -3, 1, -2.4, -5.7, 1.2),
    ("MSSP", "ED", -2.0, -4, 0, -2.2, -3.9, -0.4),
    ("CPC+", "Spending", 0.0, -1, 1, -0.2, -1.6, 1.1),
    ("CPC+", "Hosp", -1.0, -2, 0.1, -0.5, -3.7, 2.7),
    ("CPC+", "ED", -2.0, -3, -0.5, -0.6, -2.3, 1.2),
]
CONV = {  # CV trajectory by domain across rounds 0,1,2 (eFigure 1; debate not re-run)
    "Organizational structure": [0.03, 0.03, 0.03], "Regulatory pathway": [0.03, 0.02, 0.02],
    "Anti-monopoly": [0.09, 0.07, 0.07], "Ethical governance": [0.09, 0.07, 0.07],
    "AI architecture": [0.10, 0.07, 0.07], "Quality framework": [0.11, 0.09, 0.09],
    "Provider rates": [0.12, 0.08, 0.08], "SDOH integration": [0.12, 0.10, 0.10],
    "Payment structure": [0.13, 0.10, 0.10], "Rural/urban": [0.15, 0.11, 0.10],
    "Clinical model": [0.21, 0.14, 0.12], "Human oversight": [0.39, 0.25, 0.23],
}


def fig2_validation():
    sc = CANON["scenarios"]["sq_mco"]
    sim = {  # simulated S0 point estimates + 95% UI (read from canonical)
        "PMPM ($)": (sc["pmpm"]["mean"], sc["pmpm"]["p025"], sc["pmpm"]["p975"]),
        "Hosp/1,000 PY": (sc["hosp_per_1000"]["mean"], sc["hosp_per_1000"]["p025"], sc["hosp_per_1000"]["p975"]),
        "ED/1,000 PY": (sc["ed_per_1000"]["mean"], sc["ed_per_1000"]["p025"], sc["ed_per_1000"]["p975"]),
        "HEDIS gap closure (%)": (sc["hedis_gap_closure"]["mean"] * 100, sc["hedis_gap_closure"]["p025"] * 100, sc["hedis_gap_closure"]["p975"] * 100),
        "Admin (% premium)": (sc["admin_cost_pct"]["mean"] * 100, sc["admin_cost_pct"]["p025"] * 100, sc["admin_cost_pct"]["p975"] * 100),
    }
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    metrics = list(BENCH.keys())
    for i, m in enumerate(metrics):
        lo, hi = BENCH[m]
        # normalize each metric to its benchmark midpoint for a shared axis
        mid = (lo + hi) / 2
        ax1.barh(i, (hi - lo) / mid * 100, left=(lo / mid * 100), color="#cccccc", alpha=0.6, height=0.5, zorder=0)
        mean, p025, p975 = sim[m]
        ax1.errorbar(mean / mid * 100, i, xerr=[[(mean - p025) / mid * 100], [(p975 - mean) / mid * 100]],
                     fmt="o", color="#1f77b4", capsize=4, markersize=7, zorder=3)
    ax1.set_yticks(range(len(metrics)))
    ax1.set_yticklabels(metrics)
    ax1.axvline(100, color="black", linewidth=0.5, linestyle="--")
    ax1.set_xlabel("Simulated value relative to benchmark midpoint (%)")
    ax1.set_title("Panel A: Calibration vs published benchmarks")

    labels = [f"{r}: {o}" for r, o, *_ in BACKTEST]
    for i, (_, _, obs, olo, ohi, sim_v, slo, shi) in enumerate(BACKTEST):
        ax2.plot([slo, shi], [i, i], "-", color="#1f77b4", alpha=0.35, linewidth=6, zorder=1)
        ax2.plot(sim_v, i, "o", color="#1f77b4", markersize=6, zorder=3)
        ax2.errorbar(obs, i, xerr=[[obs - olo], [ohi - obs]], fmt="D", color="#d62728",
                     capsize=3, markersize=6, markeredgecolor="black", markeredgewidth=0.4, zorder=4)
    ax2.set_yticks(range(len(labels)))
    ax2.set_yticklabels(labels, fontsize=8)
    ax2.axvline(0, color="black", linewidth=0.5, linestyle="--")
    ax2.set_xlabel("Percent change vs comparator")
    ax2.set_title("Panel B: Backtesting against 5 natural experiments\n(15 of 15 observed effects within simulated 95% UI)")
    ax2.legend([plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#1f77b4", markersize=8),
                plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#d62728", markeredgecolor="black", markersize=8)],
               ["Simulated (95% UI)", "Observed (95% CI)"], loc="lower right")
    fig.suptitle("Figure 2. Calibration and External Validation", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGDIR / "Fig2.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Fig2 done")


def fig3_admin_prob():
    sweep = CANON["admin_sweep"]
    rates = [r["ai_admin_rate"] * 100 for r in sweep]
    probs = [r["prob_net_savings"] * 100 for r in sweep]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axvspan(2, 4, color="#d9ead3", alpha=0.7, zorder=0,
               label="Traditional (non-MCO) Medicaid admin (2–4%)")
    ax.plot(rates, probs, "-o", color="#1f77b4", markersize=6, linewidth=2, zorder=3)
    ax.axhline(50, color="gray", linestyle="--", linewidth=1)
    ax.axvline(7.7, color="#d62728", linestyle=":", linewidth=1.6,
               label="Status-quo MCO baseline (7.7%)")
    ax.axvline(3.0, color="#2ca02c", linestyle=":", linewidth=1.6,
               label="AI ACO target (3.0%)")
    ax.set_xlabel("AI ACO administrative overhead (% of premium)")
    ax.set_ylabel("Probability of net savings (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Figure 3. Probability of Net Savings by Administrative Cost Rate", fontweight="bold")
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGDIR / "Fig3.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Fig3 done; probs:", [round(p) for p in probs])


def efig1_convergence():
    fig, ax = plt.subplots(figsize=(10, 6))
    domains = list(CONV.keys())
    data = np.array([CONV[d] for d in domains])
    im = ax.imshow(data, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=0.4)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["Round 0", "Round 1", "Round 2"])
    ax.set_yticks(range(len(domains))); ax.set_yticklabels(domains)
    for i in range(len(domains)):
        for j in range(3):
            ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, label="Coefficient of variation")
    cbar.ax.axhline(0.15, color="black", linestyle="--", linewidth=1)
    ax.set_title("eFigure 1. Modified Delphi Convergence Trajectory\n(dashed line on colorbar = CV 0.15 threshold)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig1.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig1 done")


def efig2_equity():
    race = {r["race"]: r for r in CANON["equity_by_race"]}
    order = ["white", "black", "hispanic", "aian"]
    labels = ["White", "Black", "Hispanic", "AIAN"]
    sq = [race[r]["sq_hosp"] for r in order]
    ai = [race[r]["ai_hosp"] for r in order]
    red = [race[r]["reduction"] for r in order]
    x = np.arange(len(order))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    ax1.bar(x - 0.2, sq, 0.4, label="Status quo MCO", color="#999999")
    ax1.bar(x + 0.2, ai, 0.4, label="AI ACO", color="#1f77b4")
    ax1.set_xticks(x); ax1.set_xticklabels(labels)
    ax1.set_ylabel("Hospitalizations per 1,000 PY")
    ax1.set_title("Panel A: Hospitalization rate by group"); ax1.legend()
    ax2.bar(x, red, 0.5, color="#2ca02c")
    ax2.set_xticks(x); ax2.set_xticklabels(labels)
    ax2.set_ylabel("Absolute reduction per 1,000 PY")
    ax2.set_title("Panel B: Absolute reduction by group")
    fig.suptitle("eFigure 2. Patient Outcomes by Racial and Ethnic Group: AI ACO vs Status Quo MCO", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig2.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig2 done")


def efig3_welfare():
    w = CANON["welfare"]["ai_aco"]
    steps = [("Consumer\nsurplus", w["consumer_surplus"]),
             ("Medical\nsavings", w["medical_savings"]),
             ("Administrative\nsavings", w["admin_savings"]),
             ("Producer\nsurplus", w["producer_surplus"])]
    fig, ax = plt.subplots(figsize=(9, 6))
    cum = 0
    for label, val in steps:
        ax.bar(label, val, bottom=cum, color="#1f77b4" if val >= 0 else "#d62728")
        ax.text(label, cum + val / 2, f"${val:.0f}", ha="center", va="center", color="white", fontsize=10)
        cum += val
    ax.bar("Net social\nsurplus", cum, color="#2ca02c")
    ax.text("Net social\nsurplus", cum / 2, f"${cum:.0f}", ha="center", va="center", color="white", fontweight="bold")
    ax.set_ylabel("Per member per year ($)")
    ax.set_title("eFigure 3. Social Welfare Decomposition: AI ACO vs Status Quo MCO\n(medical + administrative savings are subcomponents of government surplus)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig3.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig3 done")


def efig4_radar():
    sc = CANON["scenarios"]
    dims = ["Hosp\nreduction", "ED\nreduction", "HEDIS\nimprovement", "Engagement", "Cost\nreduction", "Admin\nefficiency"]
    def vec(s):
        base = sc["sq_mco"]
        return [
            (base["hosp_per_1000"]["mean"] - sc[s]["hosp_per_1000"]["mean"]) / 20,
            (base["ed_per_1000"]["mean"] - sc[s]["ed_per_1000"]["mean"]) / 50,
            (sc[s]["hedis_gap_closure"]["mean"] - base["hedis_gap_closure"]["mean"]) / 0.20,
            (sc[s]["engagement_rate"]["mean"] - base["engagement_rate"]["mean"]) / 0.12,
            sc[s]["pmpm_savings"]["mean"] / 45,
            (base["admin_cost_pct"]["mean"] - sc[s]["admin_cost_pct"]["mean"]) / 0.05,
        ]
    scen_plot = [("sq_mco", "Status quo MCO", "#666666", 0.20),
                 ("enhanced_ffs", "Care coordination only", "#ff7f0e", 0.12),
                 ("ai_aco", "AI ACO consensus", "#1f77b4", 0.18),
                 ("ai_aco_universal", "AI ACO universal", "#2ca02c", 0.12)]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for s, label, color, alpha in scen_plot:
        v = vec(s); v += v[:1]
        lw = 2.5 if s == "sq_mco" else 2
        ax.plot(angles, v, "-o", color=color, linewidth=lw, markersize=4, label=label, zorder=3)
        ax.fill(angles, v, color=color, alpha=alpha, zorder=1)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(dims, fontsize=10)
    ax.set_yticklabels([])
    ax.set_title("eFigure 4. Multi-Dimensional Scenario Comparison\n(status quo MCO shown in gray; higher = better)", fontweight="bold", pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10))
    fig.savefig(FIGDIR / "eFig4.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig4 done")


if __name__ == "__main__":
    fig2_validation()
    fig3_admin_prob()
    efig1_convergence()
    efig2_equity()
    efig3_welfare()
    efig4_radar()
    print("All figures regenerated to", FIGDIR)
