#!/usr/bin/env python3
"""
Regenerate all manuscript and appendix figures for revision 2 (BMC HSR).

Revision 2: savings are net of program investment (see run_revision2.py);
Figure 3 shows the full model and the administrative-reform-only arm, and the
welfare waterfall shows the investment and the member transfer explicitly.

Design rules for this revision
------------------------------
1. NO figure numbers or figure titles are drawn inside the images. Numbering and
   captions live in the manuscript text only, which removes the class of defect
   the reviewer identified (an image internally titled "Figure 4" appearing as
   Figure 3) and removes any possibility of image/caption number drift.
2. Every element a caption refers to must actually exist in the image, and
   nothing that exists must be invisible. This is why eFigure 3 labels a thin
   bar outside the bar rather than inside it, and why eFigure 4 draws the
   status-quo reference polygon and distinguishes the consensus from the
   universal scenario, both of which previously rendered as invisible.
3. Every number is read from output/revision2/canonical_results.json at render
   time. Only inputs that the administrative re-anchoring cannot affect (the
   published validation targets and the debate convergence trajectory, neither
   of which was re-run) are embedded literals, and their sources are noted.
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent
CANON = json.load(open(ROOT / "output" / "revision2" / "canonical_results.json"))
FIGDIR = Path("/Users/sanjaybasu/waymark-local/notebooks/ai-aco/revision2/figures")
FIGDIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                     "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 10,
                     "savefig.dpi": 300})

# ---- fixed validation inputs (eTable 7/8; unaffected by the admin re-anchoring) ----
BENCH = {  # published benchmark ranges, Figure 2 panel A
    "PMPM ($)": (450, 550), "Hosp/1,000 PY": (150, 220), "ED/1,000 PY": (550, 850),
    "HEDIS gap closure (%)": (30, 45), "Admin (% premium)": (5.5, 10.1),
}
# (reform, outcome, observed, obs_lo, obs_hi, simulated, sim_lo, sim_hi)
_VAL = json.load(open(ROOT / "output" / "revision2" / "validation_results.json"))
_NM = {"oregon_cco": "Oregon CCO", "medicare_pioneer_aco": "Pioneer ACO", "chw_impact": "CHW/IMPaCT",
       "mssp": "MSSP", "cpc_plus": "CPC+"}
_OC = {"pmpm_pct_change": "Spending", "hosp_pct_change": "Hosp", "ed_pct_change": "ED"}
BACKTEST = [(_NM[r["reform"]], _OC[k], 100 * m["observed"], 100 * m["observed_95ci"][0],
             100 * m["observed_95ci"][1], 100 * m["simulated_mean"], 100 * m["simulated_95ui"][0],
             100 * m["simulated_95ui"][1])
            for r in _VAL["results"] for k, m in r["metrics"].items() if m["observed"] is not None]
CONV = {  # CV trajectory by domain across rounds 0, 1, 2 (eFigure 1; debate not re-run)
    "Organizational structure": [0.03, 0.03, 0.03], "Regulatory pathway": [0.03, 0.02, 0.02],
    "Anti-monopoly": [0.09, 0.07, 0.07], "Ethical governance": [0.09, 0.07, 0.07],
    "AI architecture": [0.10, 0.07, 0.07], "Quality framework": [0.11, 0.09, 0.09],
    "Provider rates": [0.12, 0.08, 0.08], "SDOH integration": [0.12, 0.10, 0.10],
    "Payment structure": [0.13, 0.10, 0.10], "Rural/urban": [0.15, 0.11, 0.10],
    "Clinical model": [0.21, 0.14, 0.12], "Human oversight": [0.39, 0.25, 0.23],
}

MODEL_LABEL = "Claude Sonnet 4\n(claude-sonnet-4-20250514)"


# =============================================================== Figure 1
def fig1_design():
    """Study-design schematic. Redrawn at 300 dpi; no in-image figure number."""
    C_PHASE1, C_PHASE2 = "#E8EEF7", "#E9F1E6"
    C_BOX, C_OUT, C_DIS, C_DATA = "#FFFFFF", "#CDE3C0", "#F2DFA8", "#E7EBF0"
    fig, ax = plt.subplots(figsize=(14, 8.2))
    ax.set_xlim(0, 100), ax.set_ylim(0, 100), ax.axis("off")

    def panel(x, y, w, h, fc, title):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                                    facecolor=fc, edgecolor="#666666", linewidth=1.0))
        ax.text(x + w / 2, y + h - 3.0, title, ha="center", va="center",
                fontsize=13, fontweight="bold")

    def box(x, y, w, h, head, body="", fc=C_BOX, fs=9.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45",
                                    facecolor=fc, edgecolor="#444444", linewidth=0.9))
        cy = y + h / 2
        if body:
            ax.text(x + w / 2, cy + h * 0.17, head, ha="center", va="center",
                    fontsize=fs + 0.5, fontweight="bold")
            ax.text(x + w / 2, cy - h * 0.20, body, ha="center", va="center", fontsize=fs)
        else:
            ax.text(x + w / 2, cy, head, ha="center", va="center",
                    fontsize=fs + 0.5, fontweight="bold")

    def arrow(x1, y1, x2, y2, style="-|>", ls="-", lw=1.4):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                    mutation_scale=13, linewidth=lw, linestyle=ls,
                                    color="#555555", shrinkA=1, shrinkB=1))

    panel(1, 20, 45, 78, C_PHASE1, "Phase 1: Multi-agent AI ACO design")
    panel(53, 20, 46, 78, C_PHASE2, "Phase 2: Validated microsimulation evaluation")

    box(3.5, 80, 40, 12, "8 expert AI agent personas",
        "Clinical, regulatory, actuarial, and equity perspectives\n"
        "All agents instantiated on Claude Sonnet 4\n(model claude-sonnet-4-20250514)", fs=9)
    arrow(23.5, 80, 23.5, 73)
    box(3.5, 59, 40, 13, "Modified Delphi process",
        "Iterative debate across 12 organizational domains\n"
        "Convergence: CV < 0.15 quantitative, ≥ 75% categorical", fs=9)
    arrow(13.5, 59, 13.5, 49)
    arrow(33.5, 59, 33.5, 49)
    box(3.5, 35, 19, 13, "AI ACO consensus design", "60 quantitative\nparameters", fc=C_OUT, fs=9)
    box(24.5, 35, 19, 13, "Minority dissent reports",
        "7 of 8 agents dissented\n(pessimistic scenario S3)", fc=C_DIS, fs=9)

    box(56, 85, 40, 8, "Population data (n = 75,043)",
        "ACS PUMS Medicaid adults aged 19–64, nationally weighted", fs=9)
    arrow(76, 85, 76, 81)
    box(56, 71, 40, 9, "6 evaluation scenarios",
        "Status quo MCO | AI ACO consensus, optimistic, pessimistic\n"
        "Care coordination only | Administrative only", fs=9)
    arrow(76, 71, 76, 67)
    box(56, 57, 40, 8, "5-stage microsimulation",
        "Digital access | Engagement | Utilization | Quality | Equity", fs=9)
    arrow(76, 57, 76, 53)
    box(56, 43, 40, 8,
        f"{CANON['meta']['n_iterations']:,}-iteration probabilistic sensitivity analysis",
        "Paired design; payer cost includes provider prices\nand program investment", fs=9)
    arrow(76, 43, 76, 39)
    box(56, 27, 12.4, 11, "Outcomes", "Hospitalizations\nED visits\nPMPM cost", fc="#D6E4F0", fs=8.5)
    box(69.8, 27, 12.4, 11, "Equity", "Race and\nmetropolitan\nstatus gaps", fc="#E2EFDA", fs=8.5)
    box(83.6, 27, 12.4, 11, "Welfare", "Net social\nsurplus", fc="#FCE4D6", fs=8.5)

    # Consensus parameters flow from Phase 1 into the Phase 2 scenario set along a
    # channel below every Phase 2 result box, so no connector crosses a box.
    arrow(13.0, 35, 13.0, 24, style="-")
    arrow(13.0, 24, 54.0, 24, style="-|>")
    ax.text(33.5, 25.2, "consensus parameters", fontsize=9, color="#333333", ha="center")
    arrow(34.0, 35, 34.0, 30, ls="--")
    ax.text(35.2, 31.8, "optimistic (S2), pessimistic (S3)", fontsize=8.5, color="#333333")

    box(28, 3, 48, 9, "Reform-reproduction check",
        "Model structure checked against 5 published delivery reforms", fc=C_DATA, fs=9)
    arrow(76, 12, 76, 20, ls="--")
    ax.text(77.4, 15.5, "structure check", fontsize=9, color="#555555", va="center")

    fig.savefig(FIGDIR / "Fig1.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Fig1 done")


# =============================================================== Figure 2
def fig2_validation():
    sc = CANON["scenarios"]["sq_mco"]
    sim = {
        "PMPM ($)": (sc["pmpm"]["mean"], sc["pmpm"]["p025"], sc["pmpm"]["p975"]),
        "Hosp/1,000 PY": (sc["hosp_per_1000"]["mean"], sc["hosp_per_1000"]["p025"],
                          sc["hosp_per_1000"]["p975"]),
        "ED/1,000 PY": (sc["ed_per_1000"]["mean"], sc["ed_per_1000"]["p025"],
                        sc["ed_per_1000"]["p975"]),
        "HEDIS gap closure (%)": (sc["hedis_gap_closure"]["mean"] * 100,
                                  sc["hedis_gap_closure"]["p025"] * 100,
                                  sc["hedis_gap_closure"]["p975"] * 100),
        "Admin (% premium)": (sc["admin_cost_pct"]["mean"] * 100,
                              sc["admin_cost_pct"]["p025"] * 100,
                              sc["admin_cost_pct"]["p975"] * 100),
    }
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 7))

    names = list(BENCH.keys())
    for i, k in enumerate(names):
        lo, hi = BENCH[k]
        mid = (lo + hi) / 2
        ax1.barh(i, 100 * (hi - lo) / mid, left=100 * lo / mid, height=0.45,
                 color="#d9d9d9", zorder=1)
        m, l, h = sim[k]
        ax1.errorbar(100 * m / mid, i, xerr=[[100 * (m - l) / mid], [100 * (h - m) / mid]],
                     fmt="o", color="#1f77b4", capsize=4, markersize=7, zorder=3)
    ax1.axvline(100, color="black", linewidth=0.8, linestyle="--")
    ax1.set_yticks(range(len(names)))
    ax1.set_yticklabels(names)
    ax1.set_xlabel("Simulated value as a percentage of the benchmark-range midpoint")
    ax1.set_title("Panel A: Calibration against published benchmark ranges")
    ax1.legend([plt.Rectangle((0, 0), 1, 1, color="#d9d9d9"),
                plt.Line2D([0], [0], marker="o", color="#1f77b4", linestyle="-")],
               ["Published benchmark range", "Simulated status quo (95% UI)"],
               loc="lower right")

    labels = [f"{r}: {o}" for r, o, *_ in BACKTEST]
    for i, (_, _, obs, olo, ohi, sim_v, slo, shi) in enumerate(BACKTEST):
        ax2.plot([slo, shi], [i, i], color="#9ecae1", alpha=0.9, linewidth=6, zorder=1)
        ax2.plot(sim_v, i, "o", color="#1f77b4", markersize=6, zorder=3)
        ax2.errorbar(obs, i, xerr=[[obs - olo], [ohi - obs]], fmt="D", color="#d62728",
                     capsize=3, markersize=6, markeredgecolor="black",
                     markeredgewidth=0.4, zorder=4)
    ax2.set_yticks(range(len(labels)))
    ax2.set_yticklabels(labels, fontsize=9)
    ax2.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax2.set_xlabel("Percent change versus comparator")
    ax2.set_title("Panel B: Backtesting against 5 natural experiments\n"
                  "(15 of 15 observed effects within the simulated 95% UI)")
    ax2.legend([plt.Line2D([0], [0], color="#9ecae1", linewidth=6),
                plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#1f77b4",
                           markersize=8),
                plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#d62728",
                           markeredgecolor="black", markersize=8)],
               ["Simulated 95% UI", "Simulated mean", "Observed (95% CI)"],
               loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGDIR / "Fig2.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Fig2 done")


# =============================================================== Figure 3
def fig3_admin_prob():
    full = CANON["admin_sweep"]
    adm = CANON["admin_only_sweep"]
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    ax.axvspan(2, 4, color="#d9ead3", alpha=0.7, zorder=0,
               label="Traditional (non-MCO) Medicaid administration (2–4%)")
    ax.axhline(50, color="#666666", linestyle="--", linewidth=1.4, zorder=1,
               label="50% probability")
    ax.plot([r["ai_admin_rate"] * 100 for r in adm], [r["prob_net_savings"] * 100 for r in adm],
            "-s", color="#ff7f0e", linewidth=2.4, markersize=6, zorder=3,
            label="Administrative reform only (no program investment)")
    ax.plot([r["ai_admin_rate"] * 100 for r in full], [r["prob_net_savings"] * 100 for r in full],
            "-o", color="#1f77b4", linewidth=2.4, markersize=6, zorder=3,
            label="Full AI ACO model, net of program investment")
    ax.axvline(7.7, color="#d62728", linestyle=":", linewidth=2, zorder=2,
               label="Status-quo MCO baseline (7.7%)")
    ax.axvline(3.0, color="#2ca02c", linestyle=":", linewidth=2, zorder=2,
               label="AI ACO target (3.0%)")
    ax.set_xlabel("AI ACO administrative overhead (% of premium)")
    ax.set_ylabel("Probability of net PMPM savings (%)")
    ax.set_ylim(0, 104)
    ax.set_xlim(1.8, 10.2)
    handles, labs = ax.get_legend_handles_labels()
    order = [labs.index(x) for x in [
        "Administrative reform only (no program investment)",
        "Full AI ACO model, net of program investment",
        "Traditional (non-MCO) Medicaid administration (2–4%)",
        "Status-quo MCO baseline (7.7%)", "AI ACO target (3.0%)",
        "50% probability"]]
    ax.legend([handles[i] for i in order], [labs[i] for i in order], loc="upper center",
              bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9.5)
    fig.tight_layout()
    fig.savefig(FIGDIR / "Fig3.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Fig3 done")


# =============================================================== eFigure 1
def efig1_convergence():
    doms = list(CONV.keys())
    mat = np.array([CONV[d] for d in doms])
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    im = ax.imshow(mat, cmap="RdYlGn_r", vmin=0, vmax=0.40, aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["Round 0", "Round 1", "Round 2"])
    ax.set_yticks(range(len(doms)))
    ax.set_yticklabels(doms)
    for i in range(len(doms)):
        for j in range(3):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=10)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("Coefficient of variation")
    cb.ax.plot([0, 1], [0.15, 0.15], color="black", linestyle="--", linewidth=1.6)
    cb.ax.text(1.9, 0.15, "0.15 threshold", va="center", fontsize=9, rotation=90)
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig1.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig1 done")


# =============================================================== eFigure 2
def efig2_equity():
    race = {r["race"]: r for r in CANON["equity_by_race"]}
    order = ["white", "black", "hispanic", "aian"]
    labels = ["White", "Black", "Hispanic", "AIAN"]
    sq = [race[r]["sq_hosp"] for r in order]
    ai = [race[r]["ai_hosp"] for r in order]
    red = [race[r]["reduction"] for r in order]
    x = np.arange(len(order))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8))
    ax1.bar(x - 0.2, sq, 0.4, label="Status quo MCO", color="#999999")
    ax1.bar(x + 0.2, ai, 0.4, label="AI ACO consensus", color="#1f77b4")
    ax1.set_xticks(x), ax1.set_xticklabels(labels)
    ax1.set_ylabel("Hospitalizations per 1,000 person-years")
    ax1.set_ylim(0, max(sq) * 1.28)
    ax1.set_title("Panel A: Hospitalization rate by group")
    ax1.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.0))
    ax2.bar(x, red, 0.5, color="#2ca02c")
    ax2.set_xticks(x), ax2.set_xticklabels(labels)
    ax2.set_ylabel("Absolute reduction per 1,000 person-years")
    ax2.set_title("Panel B: Absolute reduction by group")
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig2.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig2 done")


# =============================================================== eFigure 3
def efig3_welfare():
    w = CANON["welfare"]["ai_aco"]
    steps = [("Consumer\nsurplus\n(health)", w["consumer_surplus"]),
             ("Social-\nservices\ntransfer", w["consumer_transfer"]),
             ("Provider\ntransfer", w["producer_transfer"]),
             ("Administrative\nsavings", w["admin_savings"]),
             ("Medical\nsavings", w["medical_savings"]),
             ("Program\ninvestment", -w["program_investment"]),
             ("Producer\nsurplus", w["producer_surplus"])]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    cum = 0.0
    tops = []
    span = sum(abs(v) for _, v in steps)
    # A bar thinner than this fraction of the axis gets its label placed beside
    # it in dark text rather than in white text inside a 1-pixel bar.
    thin = 0.03 * span
    for label, val in steps:
        ax.bar(label, val, bottom=cum, color="#1f77b4" if val >= 0 else "#d62728")
        txt = f"${val:.0f}" if val >= 0 else f"−${abs(val):.0f}"
        if abs(val) >= thin:
            ax.text(label, cum + val / 2, txt, ha="center", va="center",
                    color="white", fontsize=11)
        else:
            ax.text(label, max(cum, cum + val) + 0.015 * span, txt, ha="center",
                    va="bottom", color="black", fontsize=11)
        cum += val
        tops.append(max(cum, cum - val))
    ax.bar("Net social\nsurplus", cum, color="#2ca02c")
    ax.text("Net social\nsurplus", cum / 2, f"${cum:.0f}", ha="center", va="center",
            color="white", fontweight="bold", fontsize=12)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Per member per year ($)")
    lows = []
    c = 0.0
    for _, v in steps:
        lows.append(min(c, c + v)); c += v
    ax.set_ylim(min(0, cum, min(lows)) * 1.1 - 50, max(tops) * 1.10)
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig3.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig3 done")


# =============================================================== eFigure 4
def efig4_radar():
    sc = CANON["scenarios"]
    dims = ["Hosp\nreduction", "ED\nreduction", "HEDIS\nimprovement",
            "Engagement", "Cost\nreduction", "Admin\nefficiency"]

    def vec(s):
        base = sc["sq_mco"]
        return [
            (base["hosp_per_1000"]["mean"] - sc[s]["hosp_per_1000"]["mean"]) / 20,
            (base["ed_per_1000"]["mean"] - sc[s]["ed_per_1000"]["mean"]) / 50,
            (sc[s]["hedis_gap_closure"]["mean"] - base["hedis_gap_closure"]["mean"]) / 0.20,
            (sc[s]["engagement_rate"]["mean"] - base["engagement_rate"]["mean"]) / 0.10,
            sc[s]["pmpm_savings"]["mean"] / 45,  # net of program investment
            (base["admin_cost_pct"]["mean"] - sc[s]["admin_cost_pct"]["mean"]) / 0.05,
        ]

    # Drawn back to front. The consensus and universal scenarios are numerically
    # near-identical, so the consensus is drawn on top with a dashed line and a
    # distinct marker: previously it was hidden entirely beneath the universal
    # polygon. The status quo is the origin of every axis by construction, so the
    # radial floor is extended below zero to make its reference polygon visible.
    series = [
        ("admin_only", "Administrative reform only", "#2ca02c", "-", "o", 2.2, 0.12),
        ("ai_aco_pessimistic", "AI ACO pessimistic", "#9467bd", ":", "d", 2.0, 0.0),
        ("enhanced_ffs", "Care coordination only", "#ff7f0e", "-", "o", 2.0, 0.14),
        ("ai_aco", "AI ACO consensus", "#1f77b4", "--", "s", 2.6, 0.0),
        ("sq_mco", "Status quo MCO (reference)", "#7f7f7f", "-", "^", 2.2, 0.10),
    ]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(9.2, 8.4), subplot_kw=dict(polar=True))
    floor = min(-0.25, min(min(vec(s)) for s, *_ in series) - 0.15)
    for s, label, color, ls, mk, lw, alpha in series:
        v = vec(s)
        v += v[:1]
        ax.plot(angles, v, linestyle=ls, marker=mk, color=color, linewidth=lw,
                markersize=5, label=label, zorder=3)
        if alpha:
            ax.fill(angles, v, color=color, alpha=alpha, zorder=1)
    ax.set_ylim(floor, max(max(vec(s)) for s, *_ in series) * 1.12)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=10)
    ax.set_yticklabels([])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(FIGDIR / "eFig4.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("eFig4 done")


if __name__ == "__main__":
    fig1_design()
    fig2_validation()
    fig3_admin_prob()
    efig1_convergence()
    efig2_equity()
    efig3_welfare()
    efig4_radar()
    print("All figures regenerated to", FIGDIR)
