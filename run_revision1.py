#!/usr/bin/env python3
"""
Unified revision-1 driver for BMC Health Services Research.

Runs the ENTIRE analysis from a single seed so every table in the manuscript
and appendix is mutually consistent (this fixes the reviewer-noted
inconsistencies where the consensus PMPM saving appeared as $41, $39, $37,
and $38.5 across different tables because they came from separate runs).

Key revision changes baked in here:
  * Status-quo admin baseline re-anchored 8.4% -> 7.7% (Milliman 2025
    Medicaid-focused composite ALR net of taxes and fees) in parameters.py.
  * All analyses use a paired design: per iteration, parameters are drawn once
    and each scenario is simulated from an identical per-iteration event RNG,
    so paired differences are clean and the discount d=0 / admin=3.0% rows
    reproduce the main consensus exactly.
  * New analyses: state/plan admin-baseline variation, program-investment
    accounting (CHW, social services, telehealth), AI deployment cost, and
    CHW-staffing engagement sensitivity.

Outputs one canonical JSON (output/revision1/canonical_results.json) plus CSVs.
"""
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from microsim.channels import simulate_scenario  # noqa: E402
from microsim.parameters import AIACOPSAParameters  # noqa: E402
from microsim.population import load_population  # noqa: E402
from microsim.welfare import compute_welfare, sensitivity_wtp  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("rev1")

OUT = ROOT / "output" / "revision1"
OUT.mkdir(parents=True, exist_ok=True)

import os
SEED = 42
N_MAIN = int(os.environ.get("REV1_N_MAIN", 1000))   # main PSA + discount + welfare (headline 95% UIs)
N_SWEEP = int(os.environ.get("REV1_N_SWEEP", 400))  # smooth sensitivity sweeps
POP_PATH = None  # uses microsim.population.load_population() default resolution

MAIN_SCENARIOS = [
    "sq_mco", "ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic",
    "enhanced_ffs", "ai_aco_universal", "admin_only",
]

# ---- program-investment assumptions (documented; revision addresses Rev2 P3) ----
CHW_LOADED_ANNUAL = 60_000.0     # loaded CHW cost/yr (BLS 2024 median ~$48k + ~25% benefits/overhead)
CHW_PER_1000 = 2.5               # consensus staffing (eTable 2)
SOCIAL_PMPM = 25.0               # consensus social-services budget (eTable 2)
TELEHEALTH_PER_MEMBER = 71.0     # one-time telehealth investment (eTable 2)
TELEHEALTH_AMORT_YEARS = 3.0


def _draw_params(psa: AIACOPSAParameters, n: int):
    """Draw n parameter sets reproducibly (scipy .rvs uses numpy global state)."""
    np.random.seed(SEED)
    return [psa.sample() for _ in range(n)]


def _paired_run(df, param_draws, scenario_fn, scenarios):
    """
    Paired PSA: for each iteration, simulate every scenario from an identical
    per-iteration RNG so differences reflect the intervention, not MC noise.

    scenario_fn(base_params, scenario) -> params dict actually simulated.
    Returns dict scenario -> DataFrame(one row per iteration).
    """
    rows = {s: [] for s in scenarios}
    for i, base in enumerate(param_draws):
        for s in scenarios:
            rng = np.random.default_rng(SEED + i)
            params = scenario_fn(base, s)
            sim_scen = params.pop("__sim_scenario__", s)
            r = simulate_scenario(df, params, sim_scen, rng)
            r["iteration"] = i
            rows[s].append(r)
    return {s: pd.DataFrame(v) for s, v in rows.items()}


def _summ(vals):
    vals = np.asarray(vals, dtype=float)
    return {
        "mean": float(np.mean(vals)),
        "p025": float(np.percentile(vals, 2.5)),
        "p975": float(np.percentile(vals, 97.5)),
        "median": float(np.median(vals)),
    }


def main():
    df = load_population(cache_path=POP_PATH) if POP_PATH else load_population()
    log.info(f"Population: {len(df):,} individuals, {df['state'].nunique()} jurisdictions, "
             f"weighted {df['PWGTP'].sum():,.0f}")

    psa = AIACOPSAParameters()
    draws = _draw_params(psa, N_MAIN)

    canonical = {
        "meta": {
            "seed": SEED, "n_iterations": N_MAIN,
            "n_individuals": int(len(df)),
            "n_jurisdictions": int(df["state"].nunique()),
            "weighted_n": float(df["PWGTP"].sum()),
            "sq_admin_baseline": "7.7% (Milliman 2025 Medicaid-focused composite ALR net of taxes/fees)",
        }
    }

    # ================================================================
    # 1. MAIN PSA (7 scenarios, paired)
    # ================================================================
    log.info("=== 1. Main PSA (7 scenarios) ===")
    def main_fn(base, s):
        p = dict(base)
        scen_map = {
            "sq_mco": "sq_mco", "ai_aco": "ai_aco",
            "ai_aco_optimistic": "ai_aco_optimistic",
            "ai_aco_pessimistic": "ai_aco_pessimistic",
            "enhanced_ffs": "enhanced_ffs",
            "ai_aco_universal": "ai_aco_universal",
            "admin_only": "admin_only",
        }
        p["__sim_scenario__"] = scen_map[s]
        return p

    main_res = _paired_run(df, draws, main_fn, MAIN_SCENARIOS)
    sq = main_res["sq_mco"]

    metrics = ["pmpm", "hosp_per_1000", "ed_per_1000", "pcp_per_1000",
               "hedis_gap_closure", "engagement_rate", "admin_cost_pct", "bw_hosp_gap"]
    scen_summary = {}
    for s, d in main_res.items():
        scen_summary[s] = {m: _summ(d[m]) for m in metrics}
        # paired PMPM savings vs sq
        sav = sq["pmpm"].values - d["pmpm"].values
        scen_summary[s]["pmpm_savings"] = _summ(sav)
        scen_summary[s]["prob_net_savings"] = float(np.mean(sav > 0))
    canonical["scenarios"] = scen_summary

    ai = main_res["ai_aco"]
    admin = main_res["admin_only"]
    sav_ai = sq["pmpm"].values - ai["pmpm"].values
    sav_admin = sq["pmpm"].values - admin["pmpm"].values
    log.info(f"  AI ACO PMPM savings ${np.mean(sav_ai):.1f} "
             f"(95% UI {np.percentile(sav_ai,2.5):.0f}-{np.percentile(sav_ai,97.5):.0f}); "
             f"admin-only ${np.mean(sav_admin):.1f}; "
             f"admin share {100*np.mean(sav_admin)/np.mean(sav_ai):.0f}%")
    log.info(f"  S0 admin {ai['admin_cost_pct'].mean():.3f}->"
             f"{sq['admin_cost_pct'].mean():.3f}; AI admin {ai['admin_cost_pct'].mean():.3f}")
    canonical["headline"] = {
        "ai_pmpm_savings": _summ(sav_ai),
        "admin_only_pmpm_savings": _summ(sav_admin),
        "admin_share_pct": float(100 * np.mean(sav_admin) / np.mean(sav_ai)),
        "clinical_component": float(np.mean(sav_ai) - np.mean(sav_admin)),
        "sq_admin_mean": float(sq["admin_cost_pct"].mean()),
        "ai_admin_mean": float(ai["admin_cost_pct"].mean()),
        "hosp_reduction": float(sq["hosp_per_1000"].mean() - ai["hosp_per_1000"].mean()),
        "ed_reduction": float(sq["ed_per_1000"].mean() - ai["ed_per_1000"].mean()),
        "hedis_sq": float(sq["hedis_gap_closure"].mean()),
        "hedis_ai": float(ai["hedis_gap_closure"].mean()),
        "engagement_sq": float(sq["engagement_rate"].mean()),
        "engagement_ai": float(ai["engagement_rate"].mean()),
    }

    # ================================================================
    # 2. WELFARE (build a summary frame compatible with welfare.py)
    # ================================================================
    log.info("=== 2. Welfare ===")
    summ_rows = []
    for s, d in main_res.items():
        row = {"scenario": s}
        for m in metrics:
            row[f"{m}_mean"] = d[m].mean()
            row[f"{m}_median"] = d[m].median()
            row[f"{m}_p025"] = d[m].quantile(0.025)
            row[f"{m}_p975"] = d[m].quantile(0.975)
        row["hedis_racial_gap_mean"] = d.get("hedis_racial_gap", pd.Series([0])).mean() if "hedis_racial_gap" in d else 0.0
        summ_rows.append(row)
    summ_df = pd.DataFrame(summ_rows)
    # welfare.py expects specific column names
    for need in ["hedis_racial_gap_mean"]:
        if need not in summ_df:
            summ_df[need] = 0.0
    welfare = compute_welfare(summ_df)
    wtp = sensitivity_wtp(summ_df)
    welfare.to_csv(OUT / "welfare.csv", index=False)
    wtp.to_csv(OUT / "wtp_sensitivity.csv", index=False)
    aci = welfare[welfare.scenario == "ai_aco"].iloc[0]
    canonical["welfare"] = {
        "ai_aco": {
            "consumer_surplus": float(aci["consumer_surplus_per_member"]),
            "govt_surplus": float(aci["govt_surplus_per_member_annual"]),
            "medical_savings": float(aci["medical_savings_per_member_annual"]),
            "admin_savings": float(aci["admin_savings_per_member_annual"]),
            "producer_surplus": float(aci["producer_surplus_per_member"]),
            "net_surplus": float(aci["net_surplus_per_member"]),
        },
        "wtp": {int(w): float(wtp[(wtp.scenario == "ai_aco") & (wtp.wtp_threshold == w)]["net_surplus_per_member"].iloc[0])
                for w in [50000, 100000, 150000, 200000]},
        "wtp_admin_only": {int(w): float(wtp[(wtp.scenario == "admin_only") & (wtp.wtp_threshold == w)]["net_surplus_per_member"].iloc[0])
                           for w in [50000, 100000, 150000, 200000]},
        "wtp_pessimistic": {int(w): float(wtp[(wtp.scenario == "ai_aco_pessimistic") & (wtp.wtp_threshold == w)]["net_surplus_per_member"].iloc[0])
                            for w in [50000, 100000, 150000, 200000]},
        "wtp_ffs": {int(w): float(wtp[(wtp.scenario == "enhanced_ffs") & (wtp.wtp_threshold == w)]["net_surplus_per_member"].iloc[0])
                    for w in [50000, 100000, 150000, 200000]},
    }
    log.info(f"  Net social surplus ${aci['net_surplus_per_member']:.0f}/member/yr "
             f"(CS {aci['consumer_surplus_per_member']:.0f}, GS {aci['govt_surplus_per_member_annual']:.0f}, "
             f"PS {aci['producer_surplus_per_member']:.0f})")

    # ================================================================
    # 3. DISCOUNT-FACTOR SWEEP (eTable 5) -- d=0 reproduces main consensus
    # ================================================================
    log.info("=== 3. Discount-factor sweep ===")
    disc_rows = []
    for d_factor in [0.0, 0.10, 0.20, 0.30, 0.40, 0.50]:
        def disc_fn(base, s, d=d_factor):
            p = dict(base)
            if s == "ai_aco":
                p = dict(base)
                p["ai_multipliers"] = {k: 1 + (v - 1) * (1 - d) for k, v in base["ai_multipliers"].items()}
                p["ai_rr"] = {t: {k: v * (1 - d) for k, v in base["ai_rr"][t].items()} for t in base["ai_rr"]}
                p["__sim_scenario__"] = "ai_aco"
            elif s == "admin_only":
                p["__sim_scenario__"] = "admin_only"
            else:
                p["__sim_scenario__"] = "sq_mco"
            return p
        res = _paired_run(df, draws, disc_fn, ["sq_mco", "ai_aco", "admin_only"])
        sqd, aid, add = res["sq_mco"], res["ai_aco"], res["admin_only"]
        sav = sqd["pmpm"].values - aid["pmpm"].values
        sav_ad = sqd["pmpm"].values - add["pmpm"].values
        disc_rows.append({
            "discount": d_factor,
            "ai_efficacy_pct": (1 - d_factor) * 100,
            "pmpm_total": float(np.mean(sav)),
            "pmpm_p025": float(np.percentile(sav, 2.5)),
            "pmpm_p975": float(np.percentile(sav, 97.5)),
            "pmpm_admin": float(np.mean(sav_ad)),
            "pmpm_clinical": float(np.mean(sav) - np.mean(sav_ad)),
            "hosp_reduction": float(sqd["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
            "ed_reduction": float(sqd["ed_per_1000"].mean() - aid["ed_per_1000"].mean()),
            "hedis_improvement": float((aid["hedis_gap_closure"].mean() - sqd["hedis_gap_closure"].mean()) * 100),
        })
    pd.DataFrame(disc_rows).to_csv(OUT / "discount_sweep.csv", index=False)
    canonical["discount_sweep"] = disc_rows
    log.info(f"  d=0 total ${disc_rows[0]['pmpm_total']:.1f} (admin ${disc_rows[0]['pmpm_admin']:.1f}); "
             f"d=0.5 total ${disc_rows[-1]['pmpm_total']:.1f}")

    # ================================================================
    # 4. ADMIN-RATE SWEEP (eTable 12)
    # ================================================================
    log.info("=== 4. Admin-rate sweep ===")
    admin_rows = []
    for r in [0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060, 0.065, 0.070, 0.077, 0.080, 0.090, 0.100]:
        def adm_fn(base, s, rr=r):
            p = dict(base)
            if s == "ai_aco":
                p["ai_admin_rate"] = rr
                p["__sim_scenario__"] = "ai_aco"
            else:
                p["__sim_scenario__"] = "sq_mco"
            return p
        res = _paired_run(df, draws[:N_SWEEP], adm_fn, ["sq_mco", "ai_aco"])
        sqd, aid = res["sq_mco"], res["ai_aco"]
        sav = sqd["pmpm"].values - aid["pmpm"].values
        admin_rows.append({
            "ai_admin_rate": r,
            "pmpm_savings": float(np.mean(sav)),
            "pmpm_p025": float(np.percentile(sav, 2.5)),
            "pmpm_p975": float(np.percentile(sav, 97.5)),
            "hosp_reduction": float(sqd["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
            "ed_reduction": float(sqd["ed_per_1000"].mean() - aid["ed_per_1000"].mean()),
            "prob_net_savings": float(np.mean(sav > 0)),
        })
    pd.DataFrame(admin_rows).to_csv(OUT / "admin_sweep.csv", index=False)
    canonical["admin_sweep"] = admin_rows

    # ================================================================
    # 5. PROVIDER-RATE SENSITIVITY (eTable 10) + ENCOUNTER SHARE x RATE (eTable 11)
    # ================================================================
    log.info("=== 5. Provider-rate + encounter-share sensitivity ===")
    def rate_share_run(rate, share):
        rows = []
        for i, base in enumerate(draws[:N_SWEEP]):
            rng = np.random.default_rng(SEED + i)
            psq = dict(base); psq["provider_rate_pct_medicare"] = 75.0
            rsq = simulate_scenario(df, psq, "sq_mco", rng)
            rng = np.random.default_rng(SEED + i)
            pai = dict(base)
            pai["provider_rate_pct_medicare"] = rate
            pai["ai_encounter_share"] = share
            pai["costs"] = dict(base["costs"]); pai["costs"]["pcp"] = base["costs"]["pcp"] * rate / 125.0
            rai = simulate_scenario(df, pai, "ai_aco", rng)
            rows.append({
                "hosp_red": rsq["hosp_per_1000"] - rai["hosp_per_1000"],
                "ed_red": rsq["ed_per_1000"] - rai["ed_per_1000"],
                "pmpm_sav": rsq["pmpm"] - rai["pmpm"],
                "hedis_imp": (rai["hedis_gap_closure"] - rsq["hedis_gap_closure"]) * 100,
            })
        d = pd.DataFrame(rows)
        return d

    from microsim.channels import referral_access_factor
    rate_rows = []
    for rate in [75, 100, 110, 125]:
        d = rate_share_run(rate, 0.58)
        rate_rows.append({
            "rate": rate,
            "referral_factor": float(referral_access_factor(rate)),
            "hosp_red": float(d["hosp_red"].mean()),
            "hosp_p025": float(d["hosp_red"].quantile(.025)), "hosp_p975": float(d["hosp_red"].quantile(.975)),
            "ed_red": float(d["ed_red"].mean()),
            "ed_p025": float(d["ed_red"].quantile(.025)), "ed_p975": float(d["ed_red"].quantile(.975)),
            "pmpm_sav": float(d["pmpm_sav"].mean()),
            "pmpm_p025": float(d["pmpm_sav"].quantile(.025)), "pmpm_p975": float(d["pmpm_sav"].quantile(.975)),
            "hedis_imp": float(d["hedis_imp"].mean()),
            "prob_net": float((d["pmpm_sav"] > 0).mean()),
        })
    full = rate_rows[-1]["pmpm_sav"]
    for rr in rate_rows:
        rr["pct_full_benefit"] = round(100 * rr["hosp_red"] / rate_rows[-1]["hosp_red"])
    canonical["rate_sensitivity"] = rate_rows

    share_rows = []
    for share in [0.20, 0.35, 0.45, 0.58, 0.75]:
        for rate in [75, 125]:
            d = rate_share_run(rate, share)
            share_rows.append({
                "share": share, "rate": rate,
                "hosp_red": float(d["hosp_red"].mean()),
                "hedis_imp": float(d["hedis_imp"].mean()),
                "pmpm_sav": float(d["pmpm_sav"].mean()),
                "prob_net": float((d["pmpm_sav"] > 0).mean()),
            })
    canonical["encounter_share"] = share_rows

    # ================================================================
    # 6. DIGITAL-DIVIDE STRATIFIED (eTable 13) from main PSA equity_race_metro
    # ================================================================
    log.info("=== 6. Digital-divide stratified ===")
    strata = ["white_metro", "white_nonmetro", "black_metro", "black_nonmetro",
              "hispanic_metro", "hispanic_nonmetro", "aian_metro", "aian_nonmetro"]
    dd_rows = []
    for st in strata:
        sq_h = np.mean([r["equity_race_metro"].get(st, {}).get("hosp_per_1000", np.nan) for r in main_res["sq_mco"].to_dict("records")])
        ai_h = np.mean([r["equity_race_metro"].get(st, {}).get("hosp_per_1000", np.nan) for r in main_res["ai_aco"].to_dict("records")])
        sq_e = np.mean([r["equity_race_metro"].get(st, {}).get("engagement_rate", np.nan) for r in main_res["sq_mco"].to_dict("records")])
        ai_e = np.mean([r["equity_race_metro"].get(st, {}).get("engagement_rate", np.nan) for r in main_res["ai_aco"].to_dict("records")])
        dd_rows.append({
            "stratum": st, "sq_hosp": float(sq_h), "ai_hosp": float(ai_h),
            "delta_hosp": float(ai_h - sq_h),
            "sq_eng": float(sq_e * 100), "ai_eng": float(ai_e * 100),
            "delta_eng_pp": float((ai_e - sq_e) * 100),
        })
    pd.DataFrame(dd_rows).to_csv(OUT / "digital_divide.csv", index=False)
    canonical["digital_divide"] = dd_rows

    # equity by race (eAppendix D / eTable)
    race_rows = []
    for race in ["white", "black", "hispanic", "aian"]:
        sq_h = np.mean([r["equity_by_race"].get(race, {}).get("hosp_per_1000", np.nan) for r in main_res["sq_mco"].to_dict("records")])
        ai_h = np.mean([r["equity_by_race"].get(race, {}).get("hosp_per_1000", np.nan) for r in main_res["ai_aco"].to_dict("records")])
        race_rows.append({"race": race, "sq_hosp": float(sq_h), "ai_hosp": float(ai_h), "reduction": float(sq_h - ai_h)})
    canonical["equity_by_race"] = race_rows

    # ================================================================
    # 7. PARAMETER IMPORTANCE (Spearman) from main PSA iteration-level deltas
    # ================================================================
    log.info("=== 7. Parameter importance ===")
    from scipy.stats import spearmanr
    # build per-iteration input frame + savings
    inp = pd.DataFrame({
        "admin_diff": [draws[i]["sq_admin_rate"] - draws[i]["ai_admin_rate"] for i in range(N_MAIN)],
        "base_hosp": [draws[i]["baseline_util"]["rising"]["hosp"] for i in range(N_MAIN)],
        "eng_mult": [draws[i]["ai_multipliers"]["outreach"] * draws[i]["ai_multipliers"]["agreement"] for i in range(N_MAIN)],
        "hosp_rr": [draws[i]["ai_rr"]["rising"]["hosp"] for i in range(N_MAIN)],
        "ed_rr": [draws[i]["ai_rr"]["rising"]["ed"] for i in range(N_MAIN)],
        "savings": sav_ai,
    })
    imp = {k: float(spearmanr(inp[k], inp["savings"]).statistic)
           for k in ["admin_diff", "base_hosp", "eng_mult", "hosp_rr", "ed_rr"]}
    canonical["parameter_importance"] = imp
    log.info(f"  Spearman admin_diff={imp['admin_diff']:.2f} base_hosp={imp['base_hosp']:.2f} eng={imp['eng_mult']:.2f}")

    # ================================================================
    # 8. NEW: STATE/PLAN ADMIN-BASELINE VARIATION (Rev1 #1)
    # ================================================================
    log.info("=== 8. State/plan admin-baseline variation ===")
    baselines = {
        "lowest_quartile_5.5": 0.055, "medicaid_focused_composite_7.7": 0.077,
        "all_plan_composite_10.1": 0.101, "highest_quartile_11.7": 0.117,
    }
    state_rows = []
    for label, b in baselines.items():
        def base_fn(base, s, bb=b):
            p = dict(base)
            if s == "sq_mco":
                p["sq_admin_rate"] = bb
                p["__sim_scenario__"] = "sq_mco"
            else:
                p["__sim_scenario__"] = "ai_aco"
            return p
        res = _paired_run(df, draws[:N_SWEEP], base_fn, ["sq_mco", "ai_aco"])
        sav = res["sq_mco"]["pmpm"].values - res["ai_aco"]["pmpm"].values
        state_rows.append({
            "baseline_label": label, "sq_admin": b,
            "pmpm_savings": float(np.mean(sav)),
            "pmpm_p025": float(np.percentile(sav, 2.5)), "pmpm_p975": float(np.percentile(sav, 97.5)),
            "prob_net": float(np.mean(sav > 0)),
        })
    pd.DataFrame(state_rows).to_csv(OUT / "state_admin_variation.csv", index=False)
    canonical["state_admin_variation"] = state_rows

    # ================================================================
    # 9. NEW: PROGRAM-INVESTMENT ACCOUNTING (Rev2 P3)
    # ================================================================
    log.info("=== 9. Program-investment accounting ===")
    chw_pmpm = CHW_PER_1000 * CHW_LOADED_ANNUAL / 1000.0 / 12.0
    tele_pmpm_amort = TELEHEALTH_PER_MEMBER / (TELEHEALTH_AMORT_YEARS * 12.0)
    tele_pmpm_yr1 = TELEHEALTH_PER_MEMBER / 12.0
    gross = float(np.mean(sav_ai))
    admin_only_sav = float(np.mean(sav_admin))
    invest_steady = chw_pmpm + SOCIAL_PMPM + tele_pmpm_amort
    invest_yr1 = chw_pmpm + SOCIAL_PMPM + tele_pmpm_yr1
    canonical["program_investment"] = {
        "chw_pmpm": chw_pmpm,
        "social_pmpm": SOCIAL_PMPM,
        "telehealth_pmpm_amortized": tele_pmpm_amort,
        "telehealth_pmpm_year1": tele_pmpm_yr1,
        "total_investment_steady": invest_steady,
        "total_investment_year1": invest_yr1,
        "gross_pmpm_savings": gross,
        "net_pmpm_savings_steady": gross - invest_steady,
        "net_pmpm_savings_year1": gross - invest_yr1,
        "admin_only_savings_no_investment": admin_only_sav,
        "note": ("Gross savings model medical+admin claims cost. Program investment "
                 "(CHW, social services, amortized telehealth) is financed within capitation "
                 "and not in modeled claims PMPM. Social-services spend is a transfer generating "
                 "consumer surplus, not deadweight. Admin-only arm requires no clinical program investment."),
    }
    log.info(f"  gross ${gross:.1f} - invest ${invest_steady:.1f} = net ${gross-invest_steady:.1f} "
             f"(admin-only ${admin_only_sav:.1f})")

    # ================================================================
    # 10. NEW: AI DEPLOYMENT COST (Rev2 P4) -- transparent bounding calc
    # ================================================================
    log.info("=== 10. AI deployment cost ===")
    ai_encounters_per_member_yr = 6.0     # AI-mediated interactions/member/yr (outreach+visits+triage)
    def ai_cost_pmpm(in_tok, out_tok, price_in, price_out, models=3):
        per_interaction = models * (in_tok / 1e6 * price_in + out_tok / 1e6 * price_out)
        return per_interaction * ai_encounters_per_member_yr / 12.0
    canonical["ai_deployment_cost"] = {
        "assumptions": {"ai_interactions_per_member_yr": ai_encounters_per_member_yr,
                        "ensemble_models": 3, "input_tokens_per_call": 30000, "output_tokens_per_call": 5000},
        "low_pmpm": round(ai_cost_pmpm(30000, 5000, 3.0, 15.0), 2),
        "mid_pmpm": round(ai_cost_pmpm(30000, 5000, 5.0, 15.0), 2),
        "high_pmpm_10x_usage": round(ai_cost_pmpm(30000, 5000, 5.0, 15.0) * 10, 2),
        "note": "Order $0.3-$3 PMPM at current API prices; well within the ~3% retained floor even at 10x usage.",
    }
    log.info(f"  AI inference ~${canonical['ai_deployment_cost']['low_pmpm']}-"
             f"{canonical['ai_deployment_cost']['high_pmpm_10x_usage']} PMPM")

    # ================================================================
    # 11. NEW: CHW-STAFFING ENGAGEMENT SENSITIVITY (Rev2 P6)
    # ================================================================
    log.info("=== 11. CHW-staffing engagement sensitivity ===")
    # Map staffing to an engagement-multiplier attenuation relative to the 3.0/1000
    # dose that the patient-advocate persona (citing Kangovi) preferred.
    chw_rows = []
    for chw, atten in [(2.0, 0.20), (2.5, 0.10), (3.0, 0.0)]:
        def chw_fn(base, s, a=atten):
            p = dict(base)
            if s == "ai_aco":
                p["ai_multipliers"] = {k: 1 + (v - 1) * (1 - a) for k, v in base["ai_multipliers"].items()}
                p["__sim_scenario__"] = "ai_aco"
            else:
                p["__sim_scenario__"] = "sq_mco"
            return p
        res = _paired_run(df, draws[:N_SWEEP], chw_fn, ["sq_mco", "ai_aco"])
        sav = res["sq_mco"]["pmpm"].values - res["ai_aco"]["pmpm"].values
        chw_rows.append({
            "chw_per_1000": chw, "engagement_attenuation": atten,
            "pmpm_savings": float(np.mean(sav)),
            "hosp_reduction": float(res["sq_mco"]["hosp_per_1000"].mean() - res["ai_aco"]["hosp_per_1000"].mean()),
            "engagement_ai": float(res["ai_aco"]["engagement_rate"].mean() * 100),
            "prob_net": float(np.mean(sav > 0)),
        })
    pd.DataFrame(chw_rows).to_csv(OUT / "chw_staffing.csv", index=False)
    canonical["chw_staffing"] = chw_rows

    # ================================================================
    # SAVE CANONICAL JSON
    # ================================================================
    with open(OUT / "canonical_results.json", "w") as f:
        json.dump(canonical, f, indent=2)
    log.info(f"Saved canonical_results.json to {OUT}")

    # Also save the full main PSA for figure regeneration
    for s, d in main_res.items():
        d.drop(columns=[c for c in ["equity_by_race", "equity_by_metro", "equity_race_metro"] if c in d],
               errors="ignore").to_parquet(OUT / f"psa_{s}.parquet", index=False)

    print("\n===== HEADLINE SUMMARY =====")
    print(json.dumps(canonical["headline"], indent=2))
    print(json.dumps(canonical["program_investment"], indent=2))


if __name__ == "__main__":
    main()
