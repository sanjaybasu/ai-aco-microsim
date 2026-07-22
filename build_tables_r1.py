#!/usr/bin/env python3
"""Generate revision-1 table markdown + inline marker values from canonical JSON."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "revision1"
C = json.load(open(OUT / "canonical_results.json"))
sc = C["scenarios"]

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
M["pmpm_sav"] = f"{C['headline']['ai_pmpm_savings']['mean']:.0f}"
M["pmpm_ui"] = f"{C['headline']['ai_pmpm_savings']['p025']:.0f} to {C['headline']['ai_pmpm_savings']['p975']:.0f}"
M["admin_only"] = f"{C['headline']['admin_only_pmpm_savings']['mean']:.0f}"
M["admin_share"] = f"{C['headline']['admin_share_pct']:.0f}"
M["prob_admin"] = f"{sc['admin_only']['prob_net_savings']*100:.1f}"
d50 = C["discount_sweep"][-1]
d0 = C["discount_sweep"][0]
M["d50_total"] = f"{d50['pmpm_total']:.0f}"
M["d50_hosp"] = f"{d50['hosp_reduction']:.0f}"
M["d50_pct"] = f"{100*d50['pmpm_total']/d0['pmpm_total']:.0f}"
M["rho_admin"] = f"{C['parameter_importance']['admin_diff']:.2f}"
M["clinical_combined_rho"] = f"{max(abs(C['parameter_importance']['base_hosp']),abs(C['parameter_importance']['eng_mult']),abs(C['parameter_importance']['hosp_rr']),abs(C['parameter_importance']['ed_rr'])):.2f}"
M["s0_admin_pct"] = f"{C['headline']['sq_admin_mean']*100:.1f}"
M["ai_admin_pct"] = f"{C['headline']['ai_admin_mean']*100:.1f}"
# program investment
pi = C["program_investment"]
M["chw_pmpm"] = f"{pi['chw_pmpm']:.0f}"
M["tele_pmpm"] = f"{pi['telehealth_pmpm_amortized']:.0f}"
M["invest_total"] = f"{pi['total_investment_steady']:.0f}"
M["net_invest"] = f"{pi['net_pmpm_savings_steady']:.1f}"
ad = C["ai_deployment_cost"]
M["ai_low"] = f"{ad['low_pmpm']:.2f}"
M["ai_mid"] = f"{ad['mid_pmpm']:.2f}"
M["ai_high"] = f"{ad['high_pmpm_10x_usage']:.1f}"
# welfare
w = C["welfare"]["ai_aco"]
M["cs"] = f"{w['consumer_surplus']:.0f}"; M["gs"] = f"{w['govt_surplus']:.0f}"
M["med_sav"] = f"{w['medical_savings']:.0f}"; M["adm_sav"] = f"{w['admin_savings']:.0f}"
M["ps"] = f"{w['producer_surplus']:.0f}"; M["net_surplus"] = f"{w['net_surplus']:.0f}"
M["net_surplus_agg"] = f"{w['net_surplus']*C['meta']['weighted_n']/1e9:.1f}"
# admin sweep specific rows
asw = {round(r["ai_admin_rate"]*100,1): r for r in C["admin_sweep"]}
M["adm6_pmpm"] = f"{asw[6.0]['pmpm_savings']:.0f}"
# pessimistic
M["pess_pmpm"] = f"{sc['ai_aco_pessimistic']['pmpm_savings']['mean']:.0f}"
M["pess_hosp"] = f"{sc['sq_mco']['hosp_per_1000']['mean']-sc['ai_aco_pessimistic']['hosp_per_1000']['mean']:.0f}"
# care coord (S4)
M["s4_pmpm"] = f"{sc['enhanced_ffs']['pmpm_savings']['mean']:.0f}"
M["s4_hosp"] = f"{sc['sq_mco']['hosp_per_1000']['mean']-sc['enhanced_ffs']['hosp_per_1000']['mean']:.0f}"
# engagement
M["eng_sq"] = f"{sc['sq_mco']['engagement_rate']['mean']*100:.0f}"
M["eng_ai"] = f"{sc['ai_aco']['engagement_rate']['mean']*100:.0f}"
M["s0_pmpm"] = f"{sc['sq_mco']['pmpm']['mean']:.0f}"
M["ai_pmpm"] = f"{sc['ai_aco']['pmpm']['mean']:.0f}"

json.dump(M, open(OUT / "markers.json", "w"), indent=2)
print("MARKERS:")
for k, v in M.items():
    print(f"  {k} = {v}")

# ---------- table builders ----------
def f0(x): return f"{x:.0f}"
def scen_row(name, key, fmt="int"):
    v = sc[key]
    return v

def build_table1():
    order = [("Status Quo MCO (S0)", "sq_mco"), ("AI ACO Consensus (S1)", "ai_aco"),
             ("AI ACO Pessimistic (S3)", "ai_aco_pessimistic"), ("Admin Reform Only (S6)", "admin_only"),
             ("Care Coord. Only (S4)", "enhanced_ffs")]
    def cell(key, metric, mult=1, dec=0):
        v = sc[key][metric]
        return f"{v['mean']*mult:.{dec}f} ({v['p025']*mult:.{dec}f}–{v['p975']*mult:.{dec}f})"
    lines = []
    lines.append("| Outcome | " + " | ".join(n for n, _ in order) + " |")
    lines.append("|" + "---|" * (len(order)+1))
    lines.append("| **Patient outcomes** | | | | | |")
    lines.append("| Hospitalizations per 1,000 PY (95% UI) | " + " | ".join(cell(k,"hosp_per_1000") for _,k in order) + " |")
    lines.append("| ED visits per 1,000 PY (95% UI) | " + " | ".join(cell(k,"ed_per_1000") for _,k in order) + " |")
    lines.append("| PCP visits per 1,000 PY (95% UI) | " + " | ".join(cell(k,"pcp_per_1000") for _,k in order) + " |")
    lines.append("| HEDIS gap closure, % (95% UI) | " + " | ".join(cell(k,"hedis_gap_closure",100) for _,k in order) + " |")
    lines.append("| Engagement rate, % (95% UI) | " + " | ".join(cell(k,"engagement_rate",100) for _,k in order) + " |")
    lines.append("| **Cost and administration** | | | | | |")
    lines.append("| PMPM, $ (95% UI) | " + " | ".join(cell(k,"pmpm") for _,k in order) + " |")
    sav = "| PMPM savings, $ (95% UI) | — | " + " | ".join(f"{sc[k]['pmpm_savings']['mean']:.0f} ({sc[k]['pmpm_savings']['p025']:.0f}–{sc[k]['pmpm_savings']['p975']:.0f})" for _,k in order[1:]) + " |"
    lines.append(sav)
    lines.append("| Admin costs, % of premium (95% UI) | " + " | ".join(cell(k,"admin_cost_pct",100,1) for _,k in order) + " |")
    return "\n".join(lines)

def build_etable5():
    lines = ["| AI Efficacy (% of Human-Trial Benchmark) | Total PMPM Savings ($) | PMPM 95% UI | Admin Component ($) | Clinical Component ($) | Hosp Reduction (per 1,000 PY) | ED Reduction (per 1,000 PY) | HEDIS Improvement (pp) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in C["discount_sweep"]:
        lines.append(f"| {r['ai_efficacy_pct']:.0f}%{' (no discount)' if r['discount']==0 else ''} | ${r['pmpm_total']:.0f} | ${r['pmpm_p025']:.0f} to ${r['pmpm_p975']:.0f} | ${r['pmpm_admin']:.0f} | ${r['pmpm_clinical']:.0f} | {r['hosp_reduction']:.1f} | {r['ed_reduction']:.1f} | {r['hedis_improvement']:.1f} |")
    return "\n".join(lines)

def build_etable12():
    lines = ["| AI ACO Admin Rate | Mean PMPM Savings | PMPM 95% UI | Hosp Reduction (per 1,000 PY) | ED Reduction (per 1,000 PY) | Probability of Net Savings |",
             "|---|---|---|---|---|---|"]
    for r in C["admin_sweep"]:
        lab = f"{r['ai_admin_rate']*100:.1f}%"
        if abs(r['ai_admin_rate']-0.03)<1e-9: lab += " (consensus target)"
        if abs(r['ai_admin_rate']-0.077)<1e-9: lab += " (status-quo baseline)"
        lines.append(f"| {lab} | ${r['pmpm_savings']:.0f} | ${r['pmpm_p025']:.0f} to ${r['pmpm_p975']:.0f} | {r['hosp_reduction']:.1f} | {r['ed_reduction']:.1f} | {r['prob_net_savings']*100:.1f}% |")
    return "\n".join(lines)

def build_etable10():
    lines = ["| Rate (% Medicare) | Referral Access Factor | Hosp Reduction per 1,000 PY (95% UI) | ED Reduction per 1,000 PY (95% UI) | PMPM Savings (95% UI) | HEDIS Improvement (pp) | % of Full Benefit |",
             "|---|---|---|---|---|---|---|"]
    labs = {75:"75% (current Medicaid)",100:"100% (Medicare parity)",110:"110%",125:"125% (debate consensus)"}
    for r in C["rate_sensitivity"]:
        lines.append(f"| {labs[r['rate']]} | {r['referral_factor']:.3f} | {r['hosp_red']:.1f} ({r['hosp_p025']:.1f}–{r['hosp_p975']:.1f}) | {r['ed_red']:.1f} ({r['ed_p025']:.1f}–{r['ed_p975']:.1f}) | ${r['pmpm_sav']:.1f} (${r['pmpm_p025']:.1f}–${r['pmpm_p975']:.1f}) | {r['hedis_imp']:.1f} | {r['pct_full_benefit']}% |")
    return "\n".join(lines)

def build_etable11():
    lines = ["| AI Encounter Share | Rate (% Medicare) | Hosp Reduction per 1,000 PY | HEDIS Improvement (pp) | PMPM Savings | Prob Net Savings |",
             "|---|---|---|---|---|---|"]
    for r in C["encounter_share"]:
        share = f"{r['share']*100:.0f}%"
        if abs(r['share']-0.58)<0.02: share += " (consensus)"
        lines.append(f"| {share} | {r['rate']}% | {r['hosp_red']:.1f} | {r['hedis_imp']:.1f} | ${r['pmpm_sav']:.1f} | {r['prob_net']*100:.0f}% |")
    return "\n".join(lines)

def build_etable13():
    nm = {"white_metro":"White, metro","white_nonmetro":"White, nonmetro","black_metro":"Black, metro",
          "black_nonmetro":"Black, nonmetro","hispanic_metro":"Hispanic, metro","hispanic_nonmetro":"Hispanic, nonmetro",
          "aian_metro":"AIAN, metro","aian_nonmetro":"AIAN, nonmetro"}
    lines = ["| Race × Metro | SQ MCO Hosp | AI ACO Hosp | Δ Hosp | SQ MCO Engagement | AI ACO Engagement | Δ Engagement (pp) |",
             "|---|---|---|---|---|---|---|"]
    for r in C["digital_divide"]:
        lines.append(f"| {nm[r['stratum']]} | {r['sq_hosp']:.0f} | {r['ai_hosp']:.0f} | {r['delta_hosp']:.0f} | {r['sq_eng']:.1f}% | {r['ai_eng']:.1f}% | +{r['delta_eng_pp']:.1f} |")
    return "\n".join(lines)

def build_etable14():
    order = [("SQ MCO","sq_mco"),("AI ACO","ai_aco"),("AI ACO Optimistic","ai_aco_optimistic"),
             ("AI ACO Pessimistic","ai_aco_pessimistic"),("Care Coord. Only","enhanced_ffs"),
             ("AI ACO Universal","ai_aco_universal"),("Admin Only","admin_only")]
    def c(k,m,mult=1,dec=0): return f"{sc[k][m]['mean']*mult:.{dec}f}"
    lines = ["| Outcome | " + " | ".join(n for n,_ in order) + " |", "|"+"---|"*(len(order)+1)]
    lines.append("| PMPM mean (95% UI) | " + " | ".join(f"${sc[k]['pmpm']['mean']:.0f} (${sc[k]['pmpm']['p025']:.0f}–${sc[k]['pmpm']['p975']:.0f})" for _,k in order) + " |")
    lines.append("| Hosp per 1,000 PY | " + " | ".join(c(k,"hosp_per_1000") for _,k in order) + " |")
    lines.append("| ED per 1,000 PY | " + " | ".join(c(k,"ed_per_1000") for _,k in order) + " |")
    lines.append("| PCP per 1,000 PY | " + " | ".join(c(k,"pcp_per_1000") for _,k in order) + " |")
    lines.append("| HEDIS gap closure | " + " | ".join(c(k,"hedis_gap_closure",100)+"%" for _,k in order) + " |")
    lines.append("| Engagement rate | " + " | ".join(c(k,"engagement_rate",100,1)+"%" for _,k in order) + " |")
    lines.append("| Admin (% of premium) | " + " | ".join(c(k,"admin_cost_pct",100,1)+"%" for _,k in order) + " |")
    return "\n".join(lines)

def build_etable17():
    pi = C["program_investment"]; ad = C["ai_deployment_cost"]
    lines = ["**Program-investment accounting (per member per month).**", "",
             "| Component | PMPM cost | Basis |", "|---|---|---|",
             f"| Community health workers (2.5 per 1,000) | ${pi['chw_pmpm']:.1f} | 2.5 per 1,000 members at ~$60,000 loaded annual cost |",
             f"| Social-services budget | ${pi['social_pmpm']:.1f} | Consensus design (eTable 2); a transfer to members (consumer surplus), not deadweight |",
             f"| Telehealth capitalization (amortized, 3 yr) | ${pi['telehealth_pmpm_amortized']:.1f} | $71 per member one-time (eTable 2), amortized |",
             f"| **Total incremental program investment (steady state)** | **${pi['total_investment_steady']:.1f}** | |",
             "", "| Savings accounting | PMPM |", "|---|---|",
             f"| Gross modeled savings (medical + administrative) | ${pi['gross_pmpm_savings']:.1f} |",
             f"| Less: program investment (steady state) | −${pi['total_investment_steady']:.1f} |",
             f"| Net payer-cost savings (full clinical-coordination model) | ${pi['net_pmpm_savings_steady']:.1f} |",
             f"| Administrative-reform-only arm (no clinical program investment) | ${pi['admin_only_savings_no_investment']:.1f} |",
             "", "**AI deployment (inference) cost.**", "",
             "| Scenario | PMPM |", "|---|---|",
             f"| Base case (3-model ensemble, ~6 AI interactions/member/yr, current token prices) | ${ad['low_pmpm']:.2f}–${ad['mid_pmpm']:.2f} |",
             f"| 10-fold usage stress | ${ad['high_pmpm_10x_usage']:.2f} |"]
    return "\n".join(lines)

def build_etable18():
    lines = ["Projected PMPM savings under alternative status-quo administrative baselines spanning the empirical Milliman 2024 distribution (holding the AI ACO target and all other parameters at consensus).", "",
             "| Status-quo baseline (source) | Baseline ALR | PMPM Savings | 95% UI | Prob Net Savings |", "|---|---|---|---|---|"]
    labs = {"lowest_quartile_5.5":"Lowest quartile of Medicaid-focused MCOs","medicaid_focused_composite_7.7":"Medicaid-focused composite (base case)",
            "all_plan_composite_10.1":"All-plan composite","highest_quartile_11.7":"Highest quartile of Medicaid-focused MCOs"}
    for r in C["state_admin_variation"]:
        lines.append(f"| {labs[r['baseline_label']]} | {r['sq_admin']*100:.1f}% | ${r['pmpm_savings']:.0f} | ${r['pmpm_p025']:.0f} to ${r['pmpm_p975']:.0f} | {r['prob_net']*100:.0f}% |")
    return "\n".join(lines)

def build_etable19():
    lines = ["Community-health-worker staffing sensitivity. Engagement multipliers are attenuated to reflect staffing below the patient-advocate persona's preferred 3.0 per 1,000 members.", "",
             "| CHW per 1,000 | Engagement multiplier attenuation | AI engagement rate | Hosp reduction per 1,000 PY | PMPM Savings | Prob Net Savings |", "|---|---|---|---|---|---|"]
    labs = {2.0:"2.0 per 1,000",2.5:"2.5 per 1,000 (consensus)",3.0:"3.0 per 1,000 (patient-advocate)"}
    for r in C["chw_staffing"]:
        lines.append(f"| {labs[r['chw_per_1000']]} | {r['engagement_attenuation']*100:.0f}% | {r['engagement_ai']:.1f}% | {r['hosp_reduction']:.1f} | ${r['pmpm_savings']:.0f} | {r['prob_net']*100:.0f}% |")
    return "\n".join(lines)

def build_etable9():
    w = C["welfare"]
    lines = ["| Scenario | WTP=$50K | WTP=$100K | WTP=$150K | WTP=$200K |", "|---|---|---|---|---|"]
    lines.append("| AI ACO net surplus per member per yr | " + " | ".join(f"${w['wtp'][k]:.0f}" for k in ['50000','100000','150000','200000']) + " |")
    lines.append("| AI ACO pessimistic | " + " | ".join(f"${w['wtp_pessimistic'][k]:.0f}" for k in ['50000','100000','150000','200000']) + " |")
    lines.append("| Care Coord. Only | " + " | ".join(f"${w['wtp_ffs'][k]:.0f}" for k in ['50000','100000','150000','200000']) + " |")
    lines.append("| Admin reform only | " + " | ".join(f"${w['wtp_admin_only'][k]:.0f}" for k in ['50000','100000','150000','200000']) + " |")
    return "\n".join(lines)

def build_equity_race():
    nm={"white":"White","black":"Black","hispanic":"Hispanic","aian":"AIAN"}
    e={r["race"]:r for r in C["equity_by_race"]}
    wgap_sq=lambda r: e[r]["sq_hosp"]-e["white"]["sq_hosp"]
    wgap_ai=lambda r: e[r]["ai_hosp"]-e["white"]["ai_hosp"]
    lines=["| Group | SQ Hosp/1,000 PY | AI ACO Hosp/1,000 PY | Absolute Reduction | Gap vs. White (SQ → AI ACO) |","|---|---|---|---|---|"]
    for r in ["white","black","hispanic","aian"]:
        gap = "—" if r=="white" else f"{wgap_sq(r):.0f} → {wgap_ai(r):.0f}"
        lines.append(f"| {nm[r]} | {e[r]['sq_hosp']:.0f} | {e[r]['ai_hosp']:.0f} | {e[r]['reduction']:.0f} | {gap} |")
    return "\n".join(lines)

tables = {"TABLE1": build_table1(), "ETABLE5": build_etable5(), "ETABLE9": build_etable9(),
          "ETABLE10": build_etable10(), "ETABLE11": build_etable11(), "ETABLE12": build_etable12(),
          "ETABLE13": build_etable13(), "ETABLE14": build_etable14(), "ETABLE17": build_etable17(),
          "ETABLE18": build_etable18(), "ETABLE19": build_etable19(), "EQUITY_RACE": build_equity_race()}
for name, t in tables.items():
    (OUT / f"table_{name}.md").write_text(t)
print("\nWrote", len(tables), "table md files to", OUT)
