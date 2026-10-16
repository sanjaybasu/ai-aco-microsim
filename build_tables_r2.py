#!/usr/bin/env python3
"""Generate revision-2 table markdown + inline marker values from canonical JSON.

Revision 2: every PMPM saving in output/revision2/canonical_results.json is net
of program investment ("pmpm" is total payer cost). Tables report net savings as
the primary quantity; gross (claims-only, pre-investment) savings appear only
where a table decomposes the net figure.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "revision2"
C = json.load(open(OUT / "canonical_results.json"))
sc = C["scenarios"]
H = C["headline"]
PI = C["program_investment"]


def usd(x, dec=0):
    """Dollar amount with a true minus sign for negatives."""
    s = f"{abs(x):,.{dec}f}"
    return f"−${s}" if round(x, dec) < 0 else f"${s}"


def num(x, dec=0):
    s = f"{abs(x):,.{dec}f}"
    return f"−{s}" if round(x, dec) < 0 else s


def pct(p, dec=0):
    return f"{p*100:.{dec}f}%"


# paired reduction UIs from psa parquets
sq = pd.read_parquet(OUT / "psa_sq_mco.parquet")
ai = pd.read_parquet(OUT / "psa_ai_aco.parquet")


def ui(a):
    return f"{np.percentile(a,2.5):.0f} to {np.percentile(a,97.5):.0f}"


hosp_red = sq["hosp_per_1000"].values - ai["hosp_per_1000"].values
ed_red = sq["ed_per_1000"].values - ai["ed_per_1000"].values

M = {}
M["hosp_red"] = f"{hosp_red.mean():.0f}"
M["hosp_ui"] = ui(hosp_red)
M["ed_red"] = f"{ed_red.mean():.0f}"
M["ed_ui"] = ui(ed_red)
M["hedis_sq"] = f"{sc['sq_mco']['hedis_gap_closure']['mean']*100:.0f}"
M["hedis_ai"] = f"{sc['ai_aco']['hedis_gap_closure']['mean']*100:.0f}"
# net (primary) and gross (decomposition) savings, full model
M["net_sav"] = num(H["ai_pmpm_savings"]["mean"])
M["net_sav_1dp"] = num(H["ai_pmpm_savings"]["mean"], 1)
M["net_ui"] = f"{num(H['ai_pmpm_savings']['p025'])} to {num(H['ai_pmpm_savings']['p975'])}"
M["prob_net_full"] = f"{H['prob_net_savings_ai']*100:.1f}"
M["gross_sav"] = f"{H['ai_pmpm_savings_gross']['mean']:.0f}"
M["gross_ui"] = f"{H['ai_pmpm_savings_gross']['p025']:.0f} to {H['ai_pmpm_savings_gross']['p975']:.0f}"
M["admin_only"] = f"{H['admin_only_pmpm_savings']['mean']:.0f}"
M["admin_only_1dp"] = f"{H['admin_only_pmpm_savings']['mean']:.1f}"
M["admin_only_ui"] = f"{num(H['admin_only_pmpm_savings']['p025'])} to {num(H['admin_only_pmpm_savings']['p975'])}"
M["admin_share_gross"] = f"{H['admin_share_pct']:.0f}"
M["clinical_gross"] = f"{H['clinical_component_gross']:.0f}"
M["prob_admin"] = f"{sc['admin_only']['prob_net_savings']*100:.1f}"
M["rho_admin"] = f"{C['parameter_importance']['admin_diff']:.2f}"
M["clinical_combined_rho"] = f"{max(abs(C['parameter_importance'][k]) for k in ['base_hosp','eng_mult','hosp_rr','ed_rr']):.2f}"
M["s0_admin_pct"] = f"{H['sq_admin_mean']*100:.1f}"
M["ai_admin_pct"] = f"{H['ai_admin_mean']*100:.1f}"
# program investment
M["chw_pmpm"] = f"{PI['chw_pmpm']:.1f}"
M["social_pmpm"] = f"{PI['social_pmpm']:.0f}"
M["tele_pmpm"] = f"{PI['telehealth_pmpm_amortized']:.1f}"
M["invest_total"] = f"{PI['total_investment_steady']:.1f}"
M["net_yr1"] = num(PI["net_pmpm_savings_year1"], 1)
ad = C["ai_deployment_cost"]
M["ai_low"] = f"{ad['low_pmpm']:.2f}"
M["ai_mid"] = f"{ad['mid_pmpm']:.2f}"
M["ai_high"] = f"{ad['high_pmpm_10x_usage']:.1f}"
# welfare
w = C["welfare"]["ai_aco"]
for k in ["consumer_surplus", "consumer_transfer", "producer_transfer", "program_investment", "govt_surplus",
          "medical_savings", "admin_savings", "producer_surplus", "net_surplus"]:
    M[f"w_{k}"] = num(w[k])
M["w_net_agg"] = f"{C['welfare']['aggregate_net_surplus_billions']:.1f}"
z = C["welfare"]["zero_transfer_bound"]
M["w0_net"] = num(z["ai_aco"]["net_surplus"])
M["w0_net_agg"] = f"{z['aggregate_net_surplus_billions']:.1f}"
wao = C["welfare"]["by_scenario"]["admin_only"]
M["w_admin_only_net"] = num(wao["net_surplus"])
# admin sweeps
asw = {round(r["ai_admin_rate"] * 100, 2): r for r in C["admin_sweep"]}
aos = {round(r["ai_admin_rate"] * 100, 2): r for r in C["admin_only_sweep"]}
for rate in [2.0, 2.5, 3.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.7, 9.0]:
    tag = str(rate).replace(".", "p")
    M[f"full_net_{tag}"] = num(asw[rate]["pmpm_savings"])
    M[f"full_prob_{tag}"] = f"{asw[rate]['prob_net_savings']*100:.0f}"
    M[f"full_gross_{tag}"] = f"{asw[rate]['pmpm_savings_gross']:.0f}"
    M[f"ao_net_{tag}"] = num(aos[rate]["pmpm_savings"], 1)
    M[f"ao_prob_{tag}"] = f"{aos[rate]['prob_net_savings']*100:.1f}"
# scenarios
for key, tag in [("ai_aco_pessimistic", "pess"), ("ai_aco_optimistic", "opt"),
                 ("enhanced_ffs", "s4")]:
    M[f"{tag}_net"] = num(sc[key]["pmpm_savings"]["mean"])
    M[f"{tag}_gross"] = f"{sc[key]['pmpm_savings_gross']['mean']:.0f}"
    M[f"{tag}_prob"] = f"{sc[key]['prob_net_savings']*100:.0f}"
    M[f"{tag}_hosp"] = f"{sc['sq_mco']['hosp_per_1000']['mean']-sc[key]['hosp_per_1000']['mean']:.0f}"
M["s4_invest"] = f"{sc['enhanced_ffs']['program_investment_pmpm']:.1f}"
# discount sweep
d0, d80, d70, d50 = (C["discount_sweep"][i] for i in (0, 2, 3, 5))
for tag, d in [("d80", d80), ("d70", d70), ("d50", d50)]:
    M[f"{tag}_net"] = num(d["pmpm_total"])
    M[f"{tag}_gross"] = f"{d['pmpm_total_gross']:.0f}"
    M[f"{tag}_clin_gross"] = f"{d['pmpm_clinical_gross']:.0f}"
    M[f"{tag}_hosp"] = f"{d['hosp_reduction']:.0f}"
    M[f"{tag}_prob"] = f"{d['prob_net_savings']*100:.0f}"
M["d_admin"] = f"{d0['pmpm_admin']:.0f}"
# engagement / pmpm levels
M["eng_sq"] = f"{sc['sq_mco']['engagement_rate']['mean']*100:.0f}"
M["eng_ai"] = f"{sc['ai_aco']['engagement_rate']['mean']*100:.0f}"
M["s0_pmpm"] = f"{sc['sq_mco']['pmpm']['mean']:.0f}"
M["ai_pmpm_total"] = f"{sc['ai_aco']['pmpm']['mean']:.0f}"
M["ai_pmpm_claims"] = f"{sc['ai_aco']['pmpm_claims']['mean']:.0f}"
# state/plan baseline variation
sv = {r["baseline_label"]: r for r in C["state_admin_variation"]}
M["sv_lo_net"] = num(sv["lowest_quartile_5.5"]["pmpm_savings"])
M["sv_lo_prob"] = f"{sv['lowest_quartile_5.5']['prob_net']*100:.0f}"
M["sv_hi_net"] = num(sv["highest_quartile_11.7"]["pmpm_savings"])
M["sv_hi_prob"] = f"{sv['highest_quartile_11.7']['prob_net']*100:.0f}"
M["sv_101_net"] = num(sv["all_plan_composite_10.1"]["pmpm_savings"])
M["sv_101_prob"] = f"{sv['all_plan_composite_10.1']['prob_net']*100:.0f}"
# CHW staffing
for r in C["chw_staffing"]:
    tag = str(r["chw_per_1000"]).replace(".", "p")
    M[f"chw_{tag}_net"] = num(r["pmpm_savings"])
    M[f"chw_{tag}_inv"] = f"{r['program_investment']:.1f}"
    M[f"chw_{tag}_hosp"] = f"{r['hosp_reduction']:.1f}"
# provider rate / encounter share
rs = {r["rate"]: r for r in C["rate_sensitivity"]}
M["rate75_net"] = num(rs[75]["pmpm_sav"])
M["rate67_net"] = num(rs[67]["pmpm_sav"])
M["rate125_net"] = num(rs[125]["pmpm_sav"])
es = {(r["share"], r["rate"]): r for r in C["encounter_share"]}
M["share20_125_net"] = num(es[(0.20, 125)]["pmpm_sav"])
M["share20_125_prob"] = f"{es[(0.20, 125)]['prob_net']*100:.0f}"
M["share_net_min"] = num(min(r["pmpm_sav"] for r in C["encounter_share"]))
M["share_net_max"] = num(max(r["pmpm_sav"] for r in C["encounter_share"]))
M["share_gross_min"] = f"{min(r['pmpm_sav_gross'] for r in C['encounter_share']):.0f}"

# racial hospitalization gaps vs White: whole population, metro, nonmetro
_e = {r["race"]: r for r in C["equity_by_race"]}
_dd = {r["stratum"]: r for r in C["digital_divide"]}
for g in ["black", "aian", "hispanic"]:
    M[f"red_{g}"] = f"{_e[g]['reduction']:.0f}"
    s_, a_ = _e[g]["sq_hosp"] - _e["white"]["sq_hosp"], _e[g]["ai_hosp"] - _e["white"]["ai_hosp"]
    M[f"gap_{g}_all"] = f"{s_:.1f} to {a_:.1f}"
    M[f"gap_{g}_all_pct"] = f"{100*(s_-a_)/s_:.1f}"
    for m_ in ["metro", "nonmetro"]:
        s_ = _dd[f"{g}_{m_}"]["sq_hosp"] - _dd[f"white_{m_}"]["sq_hosp"]
        a_ = _dd[f"{g}_{m_}"]["ai_hosp"] - _dd[f"white_{m_}"]["ai_hosp"]
        M[f"gap_{g}_{m_}"] = f"{s_:.1f} to {a_:.1f}"
        M[f"gap_{g}_{m_}_pct"] = f"{100*(s_-a_)/s_:.1f}"
M["red_white"] = f"{_e['white']['reduction']:.0f}"
_met = [r["delta_eng_pp"] for r in C["digital_divide"] if r["stratum"].endswith("_metro")]
_non = [r["delta_eng_pp"] for r in C["digital_divide"] if r["stratum"].endswith("_nonmetro")]
M["eng_gain_metro"] = f"{np.mean(_met):.1f}"
_ddl = {"white_metro": "White beneficiaries in metropolitan areas", "white_nonmetro": "White beneficiaries in nonmetropolitan areas",
        "black_metro": "Black beneficiaries in metropolitan areas", "black_nonmetro": "Black beneficiaries in nonmetropolitan areas",
        "hispanic_metro": "Hispanic beneficiaries in metropolitan areas", "hispanic_nonmetro": "Hispanic beneficiaries in nonmetropolitan areas",
        "aian_metro": "AIAN beneficiaries in metropolitan areas", "aian_nonmetro": "AIAN beneficiaries in nonmetropolitan areas"}
_ddmax = max(C["digital_divide"], key=lambda r: r["delta_eng_pp"])
M["dd_max"] = f"{_ddmax['delta_eng_pp']:.1f}"
M["dd_max_label"] = _ddl[_ddmax["stratum"]]
M["dd_min"] = f"{min(r['delta_eng_pp'] for r in C['digital_divide']):.1f}"
M["dd_aian_non"] = f"{_dd['aian_nonmetro']['delta_eng_pp']:.1f}"
M["eng_gain_nonmetro"] = f"{np.mean(_non):.1f}"

# pricing / spillover sensitivity and provider-rate cost
_S = C["pricing_spillover_sensitivity"]
for tag, key in [("hosp106", "hospital_sq_106_supplemental"), ("unpriced", "provider_rates_unpriced"),
                 ("nospill", "no_nonengaged_spillover")]:
    M[f"{tag}_net"] = num(_S[key]["pmpm_savings"])
    M[f"{tag}_prob"] = f"{_S[key]['prob_net_savings']*100:.1f}"
    M[f"{tag}_hosp"] = f"{_S[key]['hosp_reduction']:.0f}"
    M[f"{tag}_ed"] = f"{_S[key]['ed_reduction']:.0f}"
M["provider_cost"] = f"{C['provider_rate_cost_pmpm']:.0f}"
# reform-reproduction check
_V = json.load(open(OUT / "validation_results.json"))
M["val_mae"] = f"{_V['aggregate']['mean_absolute_error']*100:.1f}"
M["val_cal"] = f"{_V['aggregate']['mean_calibration_ratio']:.2f}"
M["val_cov_n"] = f"{round(_V['aggregate']['coverage_probability']*_V['aggregate']['n_comparisons'])}"
M["val_n"] = f"{int(_V['aggregate']['n_comparisons'])}"
_vr = {r["reform"]: r["metrics"] for r in _V["results"]}
for tag, ref, oc in [("or_sp", "oregon_cco", "pmpm_pct_change"), ("chw_h", "chw_impact", "hosp_pct_change"),
                     ("cpc_sp", "cpc_plus", "pmpm_pct_change")]:
    M[f"val_{tag}_obs"] = num(_vr[ref][oc]["observed"] * 100, 1)
    M[f"val_{tag}_sim"] = num(_vr[ref][oc]["simulated_mean"] * 100, 1)

# ---------- table builders ----------
ORDER5 = [("Status Quo MCO (S0)", "sq_mco"), ("AI ACO Consensus (S1)", "ai_aco"),
          ("AI ACO Pessimistic (S3)", "ai_aco_pessimistic"), ("Admin Reform Only (S6)", "admin_only"),
          ("Care Coord. Only (S4)", "enhanced_ffs")]


def build_table1():
    order = ORDER5

    def cell(key, metric, mult=1, dec=0):
        v = sc[key][metric]
        return f"{num(v['mean']*mult, dec)} ({num(v['p025']*mult, dec)} to {num(v['p975']*mult, dec)})"

    def sav(key, field):
        v = sc[key][field]
        return f"{num(v['mean'])} ({num(v['p025'])} to {num(v['p975'])})"

    n = len(order) + 1
    lines = ["| Outcome | " + " | ".join(nm for nm, _ in order) + " |", "|" + "---|" * n,
             "| *Patient outcomes* |" + " |" * len(order),
             "| Hospitalizations per 1,000 PY (95% UI) | " + " | ".join(cell(k, "hosp_per_1000") for _, k in order) + " |",
             "| ED visits per 1,000 PY (95% UI) | " + " | ".join(cell(k, "ed_per_1000") for _, k in order) + " |",
             "| PCP visits per 1,000 PY (95% UI) | " + " | ".join(cell(k, "pcp_per_1000") for _, k in order) + " |",
             "| HEDIS gap closure, % (95% UI) | " + " | ".join(cell(k, "hedis_gap_closure", 100) for _, k in order) + " |",
             "| Engagement rate, % (95% UI) | " + " | ".join(cell(k, "engagement_rate", 100) for _, k in order) + " |",
             "| *Payer cost* |" + " |" * len(order),
             "| Claims cost PMPM, \\$ (95% UI) | " + " | ".join(cell(k, "pmpm_claims") for _, k in order) + " |",
             "| Program investment PMPM, \\$ | " + " | ".join(num(sc[k]["program_investment_pmpm"], 1) for _, k in order) + " |",
             "| Total payer cost PMPM, \\$ (95% UI) | " + " | ".join(cell(k, "pmpm") for _, k in order) + " |",
             "| Net PMPM savings, \\$ (95% UI) | — | " + " | ".join(sav(k, "pmpm_savings") for _, k in order[1:]) + " |",
             "| Probability of net savings | — | " + " | ".join(pct(sc[k]["prob_net_savings"], 1) for _, k in order[1:]) + " |",
             "| Gross PMPM savings before program investment, \\$ (95% UI) | — | " + " | ".join(sav(k, "pmpm_savings_gross") for _, k in order[1:]) + " |",
             "| Admin costs, % of premium (95% UI) | " + " | ".join(cell(k, "admin_cost_pct", 100, 1) for _, k in order) + " |"]
    return "\n".join(lines)


def build_etable5():
    lines = ["| AI Efficacy (% of Human-Trial Benchmark) | Net PMPM Savings (\\$) | Net PMPM 95% UI | Probability of Net Savings | Gross PMPM Savings (\\$) | Admin Component (\\$) | Clinical Component, Gross (\\$) | Hosp Reduction (per 1,000 PY) | ED Reduction (per 1,000 PY) | HEDIS Improvement (pp) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in C["discount_sweep"]:
        lines.append(f"| {r['ai_efficacy_pct']:.0f}%{' (no discount)' if r['discount']==0 else ''} | {usd(r['pmpm_total'])} | {usd(r['pmpm_p025'])} to {usd(r['pmpm_p975'])} | {pct(r['prob_net_savings'])} | {usd(r['pmpm_total_gross'])} | {usd(r['pmpm_admin'])} | {usd(r['pmpm_clinical_gross'])} | {r['hosp_reduction']:.1f} | {r['ed_reduction']:.1f} | {r['hedis_improvement']:.1f} |")
    return "\n".join(lines)


def build_etable12():
    lines = ["| AI ACO Admin Rate | Full Model: Net PMPM Savings | Full Model: Net 95% UI | Full Model: Probability of Net Savings | Full Model: Gross PMPM Savings | Admin Reform Only: Net PMPM Savings | Admin Reform Only: Probability of Net Savings |",
             "|---|---|---|---|---|---|---|"]
    aos_ = {round(r["ai_admin_rate"], 5): r for r in C["admin_only_sweep"]}
    for r in C["admin_sweep"]:
        v = r['ai_admin_rate'] * 100
        lab = f"{v:.2f}%" if abs(v * 10 - round(v * 10)) > 1e-6 else f"{v:.1f}%"
        if abs(r['ai_admin_rate'] - 0.03) < 1e-9: lab += " (consensus target)"
        if abs(r['ai_admin_rate'] - 0.077) < 1e-9: lab += " (status-quo baseline)"
        a = aos_[round(r["ai_admin_rate"], 5)]
        lines.append(f"| {lab} | {usd(r['pmpm_savings'],1)} | {usd(r['pmpm_p025'])} to {usd(r['pmpm_p975'])} | {pct(r['prob_net_savings'],1)} | {usd(r['pmpm_savings_gross'],1)} | {usd(a['pmpm_savings'],1)} | {pct(a['prob_net_savings'],1)} |")
    return "\n".join(lines)


def build_etable10():
    lines = ["| Rate (% Medicare) | Referral Access Factor | Hosp Reduction per 1,000 PY (95% UI) | ED Reduction per 1,000 PY (95% UI) | Net PMPM Savings (95% UI) | Gross PMPM Savings | Probability of Net Savings | HEDIS Improvement (pp) | % of Full Benefit |",
             "|---|---|---|---|---|---|---|---|---|"]
    labs = {67: "67% (status-quo Medicaid primary care level)", 75: "75%", 100: "100% (Medicare parity)", 110: "110%", 125: "125% (debate consensus)"}
    for r in C["rate_sensitivity"]:
        lines.append(f"| {labs[r['rate']]} | {r['referral_factor']:.3f} | {r['hosp_red']:.1f} ({r['hosp_p025']:.1f} to {r['hosp_p975']:.1f}) | {r['ed_red']:.1f} ({r['ed_p025']:.1f} to {r['ed_p975']:.1f}) | {usd(r['pmpm_sav'],1)} ({usd(r['pmpm_p025'],1)} to {usd(r['pmpm_p975'],1)}) | {usd(r['pmpm_sav_gross'],1)} | {pct(r['prob_net'])} | {r['hedis_imp']:.1f} | {r['pct_full_benefit']}% |")
    return "\n".join(lines)


def build_etable11():
    lines = ["| AI Encounter Share | Rate (% Medicare) | Hosp Reduction per 1,000 PY | HEDIS Improvement (pp) | Net PMPM Savings | Gross PMPM Savings | Probability of Net Savings |",
             "|---|---|---|---|---|---|---|"]
    for r in C["encounter_share"]:
        share = f"{r['share']*100:.0f}%"
        if abs(r['share'] - 0.58) < 0.02: share += " (consensus)"
        lines.append(f"| {share} | {r['rate']}% | {r['hosp_red']:.1f} | {r['hedis_imp']:.1f} | {usd(r['pmpm_sav'],1)} | {usd(r['pmpm_sav_gross'],1)} | {pct(r['prob_net'])} |")
    return "\n".join(lines)


def build_etable13():
    nm = {"white_metro": "White, metro", "white_nonmetro": "White, nonmetro", "black_metro": "Black, metro",
          "black_nonmetro": "Black, nonmetro", "hispanic_metro": "Hispanic, metro", "hispanic_nonmetro": "Hispanic, nonmetro",
          "aian_metro": "AIAN, metro", "aian_nonmetro": "AIAN, nonmetro"}
    lines = ["| Race × Metro | SQ MCO Hosp | AI ACO Hosp | Δ Hosp | SQ MCO Engagement | AI ACO Engagement | Δ Engagement (pp) |",
             "|---|---|---|---|---|---|---|"]
    for r in C["digital_divide"]:
        lines.append(f"| {nm[r['stratum']]} | {r['sq_hosp']:.0f} | {r['ai_hosp']:.0f} | {num(r['delta_hosp'])} | {r['sq_eng']:.1f}% | {r['ai_eng']:.1f}% | +{r['delta_eng_pp']:.1f} |")
    return "\n".join(lines)


def build_etable14():
    order = [("SQ MCO", "sq_mco"), ("AI ACO", "ai_aco"), ("AI ACO Optimistic", "ai_aco_optimistic"),
             ("AI ACO Pessimistic", "ai_aco_pessimistic"), ("Care Coord. Only", "enhanced_ffs"),
             ("Admin Only", "admin_only")]

    def c(k, m, mult=1, dec=0): return f"{sc[k][m]['mean']*mult:.{dec}f}"

    def sv_(k, f):
        if k == "sq_mco":
            return "—"
        v = sc[k][f]
        return f"{usd(v['mean'])} ({usd(v['p025'])} to {usd(v['p975'])})"

    lines = ["| Outcome | " + " | ".join(n for n, _ in order) + " |", "|" + "---|" * (len(order) + 1)]
    lines.append("| Claims cost PMPM, mean (95% UI) | " + " | ".join(f"{usd(sc[k]['pmpm_claims']['mean'])} ({usd(sc[k]['pmpm_claims']['p025'])} to {usd(sc[k]['pmpm_claims']['p975'])})" for _, k in order) + " |")
    lines.append("| Program investment PMPM | " + " | ".join(usd(sc[k]["program_investment_pmpm"], 1) for _, k in order) + " |")
    lines.append("| Total payer cost PMPM, mean (95% UI) | " + " | ".join(f"{usd(sc[k]['pmpm']['mean'])} ({usd(sc[k]['pmpm']['p025'])} to {usd(sc[k]['pmpm']['p975'])})" for _, k in order) + " |")
    lines.append("| Net PMPM savings (95% UI) | " + " | ".join(sv_(k, "pmpm_savings") for _, k in order) + " |")
    lines.append("| Probability of net savings | " + " | ".join("—" if k == "sq_mco" else pct(sc[k]["prob_net_savings"], 1) for _, k in order) + " |")
    lines.append("| Gross PMPM savings before program investment (95% UI) | " + " | ".join(sv_(k, "pmpm_savings_gross") for _, k in order) + " |")
    lines.append("| Hosp per 1,000 PY | " + " | ".join(c(k, "hosp_per_1000") for _, k in order) + " |")
    lines.append("| ED per 1,000 PY | " + " | ".join(c(k, "ed_per_1000") for _, k in order) + " |")
    lines.append("| PCP per 1,000 PY | " + " | ".join(c(k, "pcp_per_1000") for _, k in order) + " |")
    lines.append("| HEDIS gap closure | " + " | ".join(c(k, "hedis_gap_closure", 100) + "%" for _, k in order) + " |")
    lines.append("| Engagement rate | " + " | ".join(c(k, "engagement_rate", 100, 1) + "%" for _, k in order) + " |")
    lines.append("| Admin (% of premium) | " + " | ".join(c(k, "admin_cost_pct", 100, 1) + "%" for _, k in order) + " |")
    return "\n".join(lines)


def build_etable17():
    ad = C["ai_deployment_cost"]
    by = PI["by_scenario"]
    lo, hi = PI["net_pmpm_savings_steady_ui"]
    lines = ["*Program-investment components (per member per month).*", "",
             "| Component | PMPM cost | Basis |", "|---|---|---|",
             f"| Community health workers (2.5 per 1,000) | {usd(PI['chw_pmpm'],1)} | 2.5 per 1,000 members at approximately \\$60,000 loaded annual cost |",
             f"| Social-services budget | {usd(PI['social_pmpm'],1)} | Consensus design (eTable 2); a transfer to members |",
             f"| Telehealth capitalization (amortized, 3 years) | {usd(PI['telehealth_pmpm_amortized'],1)} | \\$71 per member one-time (eTable 2), amortized over 3 years |",
             f"| Total incremental program investment (steady state) | {usd(PI['total_investment_steady'],1)} | |",
             f"| Total in year 1 (telehealth expensed, not amortized) | {usd(PI['total_investment_year1'],1)} | |",
             "", "*Program investment charged to each scenario in the simulation.*", "",
             "| Scenario | Program investment PMPM | Components |", "|---|---|---|",
             f"| S0 Status quo MCO | {usd(by['sq_mco'],1)} | None (reference) |",
             f"| S1 AI ACO consensus; S2 optimistic; S3 pessimistic | {usd(by['ai_aco'],1)} | Community health workers, social-services budget, telehealth |",
             f"| S4 Care coordination only | {usd(by['enhanced_ffs'],1)} | Care-management staff at 2.5 per 1,000 |",
             f"| S6 Administrative reform only | {usd(by['admin_only'],1)} | None (no clinical program) |",
             "", "*Full AI ACO model (S1): gross and net savings.*", "",
             "| Quantity | PMPM |", "|---|---|",
             f"| Gross PMPM savings before program investment, at the design's provider prices (95% UI) | {usd(H['ai_pmpm_savings_gross']['mean'],1)} ({usd(H['ai_pmpm_savings_gross']['p025'])} to {usd(H['ai_pmpm_savings_gross']['p975'])}) |",
             f"| Of which: payment above status-quo Medicaid prices | −${C['provider_rate_cost_pmpm']:.1f} |",
             f"| Less program investment (steady state) | −${PI['total_investment_steady']:.1f} |",
             f"| Net PMPM savings (95% UI) | {usd(PI['net_pmpm_savings_steady'],1)} ({usd(lo)} to {usd(hi)}) |",
             f"| Probability of net savings | {pct(PI['prob_net_savings_steady'],1)} |",
             f"| Net PMPM savings in year 1 (telehealth expensed) | {usd(PI['net_pmpm_savings_year1'],1)} |",
             f"| Administrative reform only (S6), net PMPM savings | {usd(H['admin_only_pmpm_savings']['mean'],1)} |",
             "", "*AI deployment (inference) cost.*", "",
             "| Scenario | PMPM |", "|---|---|",
             f"| Base case (3-model ensemble, approximately 6 AI interactions per member per year, current token prices) | \\${ad['low_pmpm']:.2f} to \\${ad['mid_pmpm']:.2f} |",
             f"| 10-fold usage stress | \\${ad['high_pmpm_10x_usage']:.2f} |"]
    return "\n".join(lines)


def build_etable18():
    lines = ["Projected net PMPM savings of the full AI ACO model under alternative status-quo administrative baselines spanning the empirical Milliman 2024 distribution (holding the AI ACO target and all other parameters at consensus).", "",
             "| Status-quo baseline (source) | Baseline ALR | Net PMPM Savings | Net 95% UI | Probability of Net Savings | Gross PMPM Savings |", "|---|---|---|---|---|---|"]
    labs = {"lowest_quartile_5.5": "Lowest quartile of Medicaid-focused MCOs", "medicaid_focused_composite_7.7": "Medicaid-focused composite (base case)",
            "all_plan_composite_10.1": "All-plan composite", "highest_quartile_11.7": "Highest quartile of Medicaid-focused MCOs"}
    for r in C["state_admin_variation"]:
        lines.append(f"| {labs[r['baseline_label']]} | {r['sq_admin']*100:.1f}% | {usd(r['pmpm_savings'])} | {usd(r['pmpm_p025'])} to {usd(r['pmpm_p975'])} | {pct(r['prob_net'])} | {usd(r['pmpm_savings_gross'])} |")
    return "\n".join(lines)


def build_etable19():
    lines = ["Community health worker staffing sensitivity. Engagement multipliers are attenuated to reflect staffing below the patient-advocate persona's preferred 3.0 per 1,000 members, and the community health worker cost in the program investment scales with staffing.", "",
             "| CHW per 1,000 | Engagement multiplier attenuation | AI engagement rate | Hosp reduction per 1,000 PY | Program investment PMPM | Net PMPM Savings | Gross PMPM Savings | Probability of Net Savings |", "|---|---|---|---|---|---|---|---|"]
    labs = {2.0: "2.0 per 1,000", 2.5: "2.5 per 1,000 (consensus)", 3.0: "3.0 per 1,000 (patient-advocate)"}
    for r in C["chw_staffing"]:
        lines.append(f"| {labs[r['chw_per_1000']]} | {r['engagement_attenuation']*100:.0f}% | {r['engagement_ai']:.1f}% | {r['hosp_reduction']:.1f} | {usd(r['program_investment'],1)} | {usd(r['pmpm_savings'],1)} | {usd(r['pmpm_savings_gross'],1)} | {pct(r['prob_net'])} |")
    return "\n".join(lines)


def build_etable9():
    w_ = C["welfare"]
    z_ = w_["zero_transfer_bound"]
    ks = ['50000', '100000', '150000', '200000']
    lines = ["| Scenario | WTP=\\$50K | WTP=\\$100K | WTP=\\$150K | WTP=\\$200K |", "|---|---|---|---|---|"]
    lines.append("| AI ACO consensus | " + " | ".join(usd(w_['wtp'][k]) for k in ks) + " |")
    lines.append("| AI ACO pessimistic | " + " | ".join(usd(w_['wtp_pessimistic'][k]) for k in ks) + " |")
    lines.append("| Care coordination only | " + " | ".join(usd(w_['wtp_ffs'][k]) for k in ks) + " |")
    lines.append("| Administrative reform only | " + " | ".join(usd(w_['wtp_admin_only'][k]) for k in ks) + " |")
    lines.append("| AI ACO consensus, transfers valued at zero | " + " | ".join(usd(z_['wtp'][k]) for k in ks) + " |")
    lines.append("| AI ACO pessimistic, transfers valued at zero | " + " | ".join(usd(z_['wtp_pessimistic'][k]) for k in ks) + " |")
    return "\n".join(lines)


def build_equity_race():
    nm = {"white": "White", "black": "Black", "hispanic": "Hispanic", "aian": "AIAN"}
    e = {r["race"]: r for r in C["equity_by_race"]}
    lines = ["| Group | SQ Hosp/1,000 PY | AI ACO Hosp/1,000 PY | Absolute Reduction | Gap vs. White (SQ → AI ACO) |", "|---|---|---|---|---|"]
    for r in ["white", "black", "hispanic", "aian"]:
        gap = "—" if r == "white" else f"{e[r]['sq_hosp']-e['white']['sq_hosp']:.0f} → {e[r]['ai_hosp']-e['white']['ai_hosp']:.0f}"
        lines.append(f"| {nm[r]} | {e[r]['sq_hosp']:.0f} | {e[r]['ai_hosp']:.0f} | {e[r]['reduction']:.0f} | {gap} |")
    return "\n".join(lines)


def build_etable20():
    L = C["legal_liability_sensitivity"]
    lines = ["| Incremental legal/liability reserve (pp of premium) | Effective AI ACO admin rate | "
             "Admin reform only: net PMPM savings | Admin reform only: probability of net savings | "
             "Full model: net PMPM savings | Full model: probability of net savings | Full model: gross PMPM savings |",
             "|---|---|---|---|---|---|---|"]
    for r in L["rows"]:
        lines.append(
            f"| {r['legal_reserve_pp_of_premium']:.2f} | {r['effective_admin_rate']*100:.2f}% | "
            f"{usd(r['admin_only_pmpm_savings'],1)} | {pct(r['admin_only_prob_net_savings'])} | "
            f"{usd(r['full_model_pmpm_net_of_investment'],1)} | {pct(r['full_model_prob_net_savings'])} | "
            f"{usd(r['full_model_pmpm_savings_gross'],1)} |")
    return "\n".join(lines)


def build_etable21():
    g = C["greylit_ai_admin_anchor"]
    lines = ["| Assumed AI-attributable reduction in payer administrative cost | "
             "Implied administrative rate (% of premium) | Admin reform only: net PMPM savings | "
             "Admin reform only: probability of net savings | Full model: net PMPM savings | "
             "Full model: probability of net savings | Full model: gross PMPM savings |",
             "|---|---|---|---|---|---|---|"]
    for _, s in g["scenarios"].items():
        lines.append(
            f"| {s['assumed_ai_admin_reduction_pct']:.0f}% of administrative cost | "
            f"{s['grid_rate_used']*100:.1f}% | {usd(s['admin_only_pmpm_savings'],1)} | "
            f"{pct(s['admin_only_prob_net_savings'])} | {usd(s['pmpm_savings'],1)} | "
            f"{pct(s['prob_net_savings'])} | {usd(s['pmpm_savings_gross'],1)} |")
    lines.append(f"| Consensus design target (AI plus nonprofit organizational form) | 3.0% | "
                 f"{usd(H['admin_only_pmpm_savings']['mean'],1)} | {pct(H['prob_net_savings_admin_only'])} | "
                 f"{usd(H['ai_pmpm_savings']['mean'],1)} | {pct(H['prob_net_savings_ai'])} | "
                 f"{usd(H['ai_pmpm_savings_gross']['mean'],1)} |")
    return "\n".join(lines)


def build_etable8():
    names = {"oregon_cco": "Oregon CCO (2012–2015)", "medicare_pioneer_aco": "Medicare Pioneer ACO (2012–2014)",
             "chw_impact": "CHW IMPaCT trials (pooled)", "mssp": "MSSP (2012–2015 physician-group)",
             "cpc_plus": "CPC+ (5-year evaluation)"}
    P = _V["parameters"]
    a = ["| Reform | Engagement multipliers (outreach, agreement, engagement, adherence) | Hosp RR (low / rising / high risk) | ED RR (low / rising / high risk) | Admin rate relative to status quo | Spillover to non-engaged members (hosp, ED) | Cost reduction among engaged members | Primary care visit increase (engaged) |",
         "|---|---|---|---|---|---|---|---|"]
    for r, nm in names.items():
        q = P[r]; m = q["multipliers"]
        a.append(f"| {nm} | {m['outreach']:.2f}×, {m['agreement']:.2f}×, {m['engagement']:.2f}×, {m['adherence']:.2f}× | "
                 f"{q['rr']['low']['hosp']:.2f} / {q['rr']['rising']['hosp']:.2f} / {q['rr']['high']['hosp']:.2f} | "
                 f"{q['rr']['low']['ed']:.2f} / {q['rr']['rising']['ed']:.2f} / {q['rr']['high']['ed']:.2f} | "
                 f"{q['admin_factor_vs_sq']:.2f}× | {100*(1-q['spillover_hosp']):.0f}%, {100*(1-q['spillover_ed']):.0f}% | "
                 f"{100*(1-q['cost_reduction_engaged']):.0f}% | {100*q['pcp_increase']:.0f}% |")
    b = ["| Reform | Outcome | Observed | Observed 95% CI | Simulated | Simulated 95% UI | Observed in UI |",
         "|---|---|---|---|---|---|---|"]
    lab = {"pmpm_pct_change": "Spending", "hosp_pct_change": "Hospitalizations", "ed_pct_change": "ED visits"}
    pc = lambda x: f"{num(x*100,1)}%"
    for res in _V["results"]:
        for oc, m in res["metrics"].items():
            if m["observed"] is None:
                continue
            lo, hi = m["observed_95ci"]
            b.append(f"| {names[res['reform']]} | {lab[oc]} | {pc(m['observed'])} | ({pc(lo)}, {pc(hi)}) | "
                     f"{pc(m['simulated_mean'])} | ({pc(m['simulated_95ui'][0])}, {pc(m['simulated_95ui'][1])}) | "
                     f"{'Yes' if m['coverage'] else 'No'} |")
    return "\n".join(a), "\n".join(b)


def build_welfare_decomp():
    w_ = C["welfare"]["ai_aco"]
    z_ = C["welfare"]["zero_transfer_bound"]["ai_aco"]
    return "\n".join([
        "| Component | Per Member Per Year |", "|---|---|",
        f"| Consumer surplus (QALY gains) | {usd(w_['consumer_surplus'])} |",
        f"| Consumer surplus (social-services transfer, valued at face value) | {usd(w_['consumer_transfer'])} |",
        f"| Government surplus (net payer savings) | {usd(w_['govt_surplus'])} |",
        f"| — of which: medical savings | {usd(w_['medical_savings'])} |",
        f"| — of which: administrative savings | {usd(w_['admin_savings'])} |",
        f"| — of which: program investment | {usd(-w_['program_investment'])} |",
        f"| Producer surplus (primary care volume) | {usd(w_['producer_surplus'])} |",
        f"| Producer transfer (payment above status-quo prices, valued at face value) | {usd(w_['producer_transfer'])} |",
        f"| Net social surplus | {usd(w_['net_surplus'])} |",
        f"| Net social surplus with both transfers valued at zero | {usd(z_['net_surplus'])} |",
    ])


def build_spearman():
    pi = C["parameter_importance"]
    return "\n".join([
        "| Parameter | Source type | Spearman ρ | Contribution |", "|---|---|---|---|",
        f"| Administrative cost rate difference | Mixed (status quo empirical, Milliman; AI ACO rate assumed) | {pi['admin_diff']:.2f} | Dominant |",
        f"| Baseline utilization rates | Empirical (MEPS/HCUP) | {pi['base_hosp']:.2f} | Modest |",
        f"| Engagement multiplier | Mixed (SQ empirical; AI multipliers projected) | {pi['eng_mult']:.2f} | Modest |",
        f"| AI ED RR reduction | Projected (anchored to Oregon CCO) | {pi['ed_rr']:.2f} | Minor |",
        f"| AI hospitalization RR reduction | Projected (anchored to ACO natural experiments) | {pi['hosp_rr']:.2f} | Negligible |",
    ])


# --- markers carried from revision 1 ------------------------------------------
_L = C["legal_liability_sensitivity"]
_G = C["greylit_ai_admin_anchor"]
_MC = C["monte_carlo_stability"]
M["n_iter"] = f"{C['meta']['n_iterations']:,}"
M["mcse_pmpm"] = f"{_MC['mcse_ai_pmpm_savings']:.2f}"
M["mcse_admin"] = f"{_MC['mcse_admin_pmpm_savings']:.2f}"
M["run_to_run_total"] = f"{_MC['ai_pmpm_abs_diff']:.2f}"
M["run_to_run_admin"] = f"{_MC['admin_pmpm_abs_diff']:.2f}"
M["legal_breakeven_pp"] = f"{_L['breakeven_reserve_pp_admin_only']:.1f}"
M["legal_breakeven_pmpm"] = f"{_L['breakeven_reserve_pmpm_admin_only']:.0f}"
_l1 = [r for r in _L["rows"] if abs(r["legal_reserve_pp_of_premium"] - 1.0) < 1e-6][0]
M["legal_1pp_admin_only"] = f"{_l1['admin_only_pmpm_savings']:.1f}"
M["legal_1pp_admin_only_prob"] = f"{_l1['admin_only_prob_net_savings']*100:.0f}"
M["legal_1pp_full_net"] = num(_l1["full_model_pmpm_net_of_investment"], 1)
M["legal_1pp_full_gross"] = f"{_l1['full_model_pmpm_savings_gross']:.1f}"
for tag, key in [("lo", "ai_only_8pct"), ("hi", "ai_only_14pct")]:
    s_ = _G["scenarios"][key]
    M[f"greylit_rate_{tag}"] = f"{s_['grid_rate_used']*100:.1f}"
    M[f"greylit_full_net_{tag}"] = num(s_["pmpm_savings"])
    M[f"greylit_full_gross_{tag}"] = f"{s_['pmpm_savings_gross']:.0f}"
    M[f"greylit_full_prob_{tag}"] = f"{s_['prob_net_savings']*100:.0f}"
    M[f"greylit_admin_only_{tag}"] = f"{s_['admin_only_pmpm_savings']:.0f}"
    M[f"greylit_admin_only_prob_{tag}"] = f"{s_['admin_only_prob_net_savings']*100:.0f}"
json.dump(M, open(OUT / "markers.json", "w"), indent=2)

tables = {"TABLE1": build_table1(), "ETABLE5": build_etable5(), "ETABLE9": build_etable9(),
          "ETABLE10": build_etable10(), "ETABLE11": build_etable11(), "ETABLE12": build_etable12(),
          "ETABLE13": build_etable13(), "ETABLE14": build_etable14(), "ETABLE17": build_etable17(),
          "ETABLE18": build_etable18(), "ETABLE19": build_etable19(),
          "ETABLE20": build_etable20(), "ETABLE21": build_etable21(),
          "EQUITY_RACE": build_equity_race(), "WELFARE_DECOMP": build_welfare_decomp(),
          "ETABLE8_PARAMS": build_etable8()[0], "ETABLE8_RESULTS": build_etable8()[1],
          "SPEARMAN": build_spearman()}
for name, t in tables.items():
    (OUT / f"table_{name}.md").write_text(t)
print("Wrote", len(tables), "table md files to", OUT)
print(json.dumps(M, indent=2))
