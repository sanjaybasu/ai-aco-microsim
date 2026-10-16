#!/usr/bin/env python3
"""
Unified revision-2 driver for BMC Health Services Research.

Revision 2 changes relative to run_revision1.py:
  * Program investment is part of the modeled payer cost from the start. The
    engine adds each scenario's incremental program investment (community health
    workers, social-services budget, amortized telehealth for the
    clinical-coordination scenarios; care-management staff for care coordination
    without AI; none for the status quo or the administrative-reform-only arm) to
    the simulated PMPM, so "pmpm" is total payer cost and every saving, interval
    and probability below is NET of program investment. Gross (claims-only)
    savings are carried alongside for the decomposition.
  * Welfare counts the social-services budget as a transfer to members (face
    value), with a conservative bound that values it at zero.
  * The administrative-rate grid adds 2.0% and 2.5% to locate where the full
    model reaches net savings.

Parameter draws, seeds and iteration counts are identical to revision 1, so
gross savings reproduce the revision-1 values exactly.

Revision-1 notes follow.

Runs the ENTIRE analysis at a single seed so that every table in the manuscript
and appendix is mutually consistent (this fixes the reviewer-noted
inconsistencies in which the consensus PMPM saving appeared as $41, $39, $37 and
$38.5 across different tables produced by different runs).

Key revision changes baked in here:
  * Status-quo administrative baseline re-anchored 8.4% -> 7.7% (Milliman 2025
    Medicaid-focused composite ALR net of taxes and fees) in parameters.py.
  * All analyses use a paired design: per iteration, parameters are drawn once
    and every scenario is simulated from an identical per-iteration event RNG,
    so paired differences are clean and the base-case cell of every sweep is
    the *same cell* as the main analysis.
  * Iteration count raised and made uniform across the main analysis and every
    sweep (REV1_N, default 2000), which (a) halves the Monte Carlo standard
    error relative to the previous 1,000-iteration run and (b) makes base-case
    rows of eTable 5, eTable 12, eTable 18 and eTable 20 reproduce Table 1
    exactly rather than approximately.
  * A replicate at an independent seed quantifies run-to-run stability, which
    is reported so readers can see the residual Monte Carlo error directly.
  * New analyses: administrative-baseline variation across the empirical
    Milliman distribution, program-investment accounting (community health
    workers, social services, telehealth), AI deployment cost, community
    health worker staffing sensitivity, and a legal/liability reserve
    sensitivity.

Outputs one canonical JSON (output/revision1/canonical_results.json) plus CSVs.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from microsim.parameters import AIACOPSAParameters  # noqa: E402
from microsim.population import load_population  # noqa: E402
from microsim.welfare import compute_welfare, sensitivity_wtp  # noqa: E402
from rev1_engine import Engine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("rev1")

OUT = ROOT / "output" / "revision2"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
SEED_REPLICATE = 20260726          # independent seed, run-to-run stability check
N = int(os.environ.get("REV1_N", 2000))          # uniform iteration count
N_REP = int(os.environ.get("REV1_N_REP", 2000))  # replicate iterations
POP_PATH = "/Users/sanjaybasu/waymark-local/packaging/medicaid-frailty-bias/data/acs_pums_medicaid_adults.parquet"

MAIN_SCENARIOS = [
    "sq_mco", "ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic",
    "enhanced_ffs", "admin_only",
]

# ---- program-investment assumptions (documented; addresses Reviewer 2 P3) ----
CHW_LOADED_ANNUAL = 60_000.0     # loaded CHW cost/yr (BLS 2024 median ~$48k + ~25% benefits/overhead)
CHW_PER_1000 = 2.5               # consensus staffing (eTable 2)
SOCIAL_PMPM = 25.0               # consensus social-services budget (eTable 2)
TELEHEALTH_PER_MEMBER = 71.0     # one-time telehealth investment (eTable 2)
TELEHEALTH_AMORT_YEARS = 3.0
PROGRAM_INVESTMENT = {
    "chw_loaded_annual": CHW_LOADED_ANNUAL,
    "chw_pmpm": CHW_PER_1000 * CHW_LOADED_ANNUAL / 1000.0 / 12.0,
    "social_pmpm": SOCIAL_PMPM,
    "telehealth_pmpm": TELEHEALTH_PER_MEMBER / (TELEHEALTH_AMORT_YEARS * 12.0),
}

# ---- administrative-rate sweep grid -----------------------------------------
# Includes the consensus target (3.0%), the legal/liability reserve increments
# (3.25%-6.0%), the range implied by published payer AI administrative-savings
# estimates applied to the 7.7% baseline (6.6% and 7.1%), the lowest-quartile
# Milliman benchmark (5.5%) and the status-quo baseline (7.7%).
ADMIN_GRID = [0.020, 0.025, 0.030, 0.0325, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060, 0.065,
              0.066, 0.070, 0.071, 0.077, 0.080, 0.090, 0.100]

# Legal/liability reserve sensitivity, expressed as percentage points of premium
# added on top of the 3.0% retained administrative floor.  A reserve is simply an
# additional administrative percentage point, so its effect is read directly off
# the administrative-rate curve rather than requiring separate machinery.
LEGAL_RESERVE_PP = [0.0, 0.0025, 0.005, 0.010, 0.020, 0.030]

DISCOUNTS = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50]
ADMIN_BASELINES = {
    "lowest_quartile_5.5": 0.055,
    "medicaid_focused_composite_7.7": 0.077,
    "all_plan_composite_10.1": 0.101,
    "highest_quartile_11.7": 0.117,
}
# Engagement multipliers are anchored to community health worker trials at the
# patient-advocate staffing of 3.0 per 1,000; the consensus design staffs 2.5 per
# 1,000, so the main analysis attenuates the multipliers by 10% (CHW_MAIN_ATTEN).
# Rows give (staffing, total attenuation, attenuation relative to the main draw).
CHW_MAIN_ATTEN = 0.10
CHW_STAFFING = [(2.0, 0.20, 1 - 0.8 / 0.9), (2.5, 0.10, 0.0), (3.0, 0.0, 1 - 1 / 0.9)]

# Provider payment pricing (% of Medicare). Status-quo Medicaid price levels:
# primary care 67% (Zuckerman, Skopec, Aarons, Health Aff 2021;40:343-8, 2019 fee
# index); inpatient base payment 78% (MACPAC, Medicaid Hospital Payment: A
# Comparison across States and to Medicare, April 2017). AI ACO design: 125% PCP,
# 110% hospital. Sensitivity: hospital status quo at 106% (MACPAC, net of
# supplemental payments and provider contributions).
PRICING = {"price_provider_rates": True, "sq_pcp_rate_pct": 67.0,
           "sq_hosp_rate_pct": 78.0, "ai_hosp_rate_pct": 110.0}
RATE_GRID = [67, 75, 100, 110, 125]
SHARE_GRID = [0.20, 0.35, 0.45, 0.58, 0.75]

METRICS = ["pmpm", "pmpm_claims", "program_investment_pmpm", "social_transfer_pmpm", "provider_uplift_pmpm",
           "hosp_per_1000", "ed_per_1000", "pcp_per_1000",
           "hedis_gap_closure", "engagement_rate", "admin_cost_pct", "bw_hosp_gap"]


def _draw_params(psa, n, seed):
    """Draw n parameter sets reproducibly (scipy .rvs uses numpy global state)."""
    np.random.seed(seed)
    return [psa.sample(clip_admin=False, sample_racial_penalty=True) for _ in range(n)]


def _summ(vals):
    vals = np.asarray(vals, dtype=float)
    return {
        "mean": float(np.mean(vals)),
        "p025": float(np.percentile(vals, 2.5)),
        "p975": float(np.percentile(vals, 97.5)),
        "median": float(np.median(vals)),
        "mcse": float(np.std(vals, ddof=1) / np.sqrt(len(vals))),
    }


def _spec_discount(d):
    """d == 0 maps to the unmodified base draw so the d=0 row IS the main cell."""
    return None if d == 0 else {"kind": "discount", "d": d}


def _spec_chw(atten, per_1000):
    """The consensus staffing with no attenuation is the unmodified main cell."""
    if atten == 0 and per_1000 == CHW_PER_1000:
        return None
    return {"kind": "chw", "atten": atten, "per_1000": per_1000}


def _gross(sq_df, d):
    """Claims-only (pre-investment) paired savings."""
    return sq_df["pmpm_claims"].values - d["pmpm_claims"].values


def main():
    t0 = time.time()
    df = load_population(cache_path=POP_PATH)
    log.info(f"Population: {len(df):,} individuals, {df['state'].nunique()} jurisdictions, "
             f"weighted {df['PWGTP'].sum():,.0f}")

    psa = AIACOPSAParameters()
    draws = _draw_params(psa, N, SEED)
    draws_rep = _draw_params(psa, N_REP, SEED_REPLICATE)
    for d in draws + draws_rep:
        d["program_investment"] = dict(PROGRAM_INVESTMENT)
        d.update(PRICING)
        d["s4_admin_factor"] = 1.0       # care coordination without AI keeps status-quo administration
        d["r2_scenarios"] = True         # S2/S3 use their minority-report parameters
        d["ai_multipliers"] = {k: 1 + (v - 1) * (1 - CHW_MAIN_ATTEN)
                               for k, v in d["ai_multipliers"].items()}

    canonical = {
        "meta": {
            "seed": SEED,
            "seed_replicate": SEED_REPLICATE,
            "n_iterations": N,
            "n_iterations_replicate": N_REP,
            "uniform_iterations_across_sweeps": True,
            "n_individuals": int(len(df)),
            "n_jurisdictions": int(df["state"].nunique()),
            "weighted_n": float(df["PWGTP"].sum()),
            "sq_admin_baseline": "7.7% (Milliman 2025 Medicaid-focused composite ALR net of taxes/fees)",
        }
    }

    with Engine(POP_PATH,
                {"main": draws, "rep": draws_rep},
                {"main": SEED, "rep": SEED_REPLICATE}) as eng:

        # ============================================================
        # 1. MAIN PSA (7 scenarios, paired)
        # ============================================================
        log.info("=== 1. Main PSA (7 scenarios) ===")
        main_res = {s: eng.cell(s, N) for s in MAIN_SCENARIOS}
        sq = main_res["sq_mco"]
        ai = main_res["ai_aco"]
        admin = main_res["admin_only"]

        scen_summary = {}
        for s, d in main_res.items():
            scen_summary[s] = {m: _summ(d[m]) for m in METRICS}
            sav = sq["pmpm"].values - d["pmpm"].values
            scen_summary[s]["pmpm_savings"] = _summ(sav)
            scen_summary[s]["prob_net_savings"] = float(np.mean(sav > 0))
            gsav = _gross(sq, d)
            scen_summary[s]["pmpm_savings_gross"] = _summ(gsav)
            scen_summary[s]["prob_gross_savings"] = float(np.mean(gsav > 0))
            scen_summary[s]["program_investment_pmpm"] = float(d["program_investment_pmpm"].mean())
        canonical["scenarios"] = scen_summary

        sav_ai = sq["pmpm"].values - ai["pmpm"].values
        sav_admin = sq["pmpm"].values - admin["pmpm"].values
        log.info(f"  AI ACO PMPM savings ${np.mean(sav_ai):.2f} "
                 f"(95% UI {np.percentile(sav_ai,2.5):.0f}-{np.percentile(sav_ai,97.5):.0f}); "
                 f"admin-only ${np.mean(sav_admin):.2f}; "
                 f"admin share {100*np.mean(sav_admin)/np.mean(sav_ai):.0f}%")
        gsav_ai = _gross(sq, ai)
        canonical["headline"] = {
            "ai_pmpm_savings": _summ(sav_ai),
            "ai_pmpm_savings_gross": _summ(gsav_ai),
            "prob_gross_savings_ai": float(np.mean(gsav_ai > 0)),
            "ai_program_investment": float(ai["program_investment_pmpm"].mean()),
            "admin_only_pmpm_savings": _summ(sav_admin),
            "admin_share_pct": float(100 * np.mean(sav_admin) / np.mean(gsav_ai)),
            "clinical_component_gross": float(np.mean(gsav_ai) - np.mean(sav_admin)),
            "sq_admin_mean": float(sq["admin_cost_pct"].mean()),
            "ai_admin_mean": float(ai["admin_cost_pct"].mean()),
            "hosp_reduction": float(sq["hosp_per_1000"].mean() - ai["hosp_per_1000"].mean()),
            "ed_reduction": float(sq["ed_per_1000"].mean() - ai["ed_per_1000"].mean()),
            "hedis_sq": float(sq["hedis_gap_closure"].mean()),
            "hedis_ai": float(ai["hedis_gap_closure"].mean()),
            "engagement_sq": float(sq["engagement_rate"].mean()),
            "engagement_ai": float(ai["engagement_rate"].mean()),
            "prob_net_savings_ai": float(np.mean(sav_ai > 0)),
            "prob_net_savings_admin_only": float(np.mean(sav_admin > 0)),
        }

        # ============================================================
        # 1b. REPLICATE AT AN INDEPENDENT SEED (Monte Carlo stability)
        # ============================================================
        log.info("=== 1b. Replicate at independent seed ===")
        sq_r = eng.cell("sq_mco", N_REP, draw_set="rep")
        ai_r = eng.cell("ai_aco", N_REP, draw_set="rep")
        ad_r = eng.cell("admin_only", N_REP, draw_set="rep")
        sav_ai_r = sq_r["pmpm"].values - ai_r["pmpm"].values
        sav_admin_r = sq_r["pmpm"].values - ad_r["pmpm"].values
        canonical["monte_carlo_stability"] = {
            "n_per_run": N,
            "ai_pmpm_savings_run1": float(np.mean(sav_ai)),
            "ai_pmpm_savings_run2": float(np.mean(sav_ai_r)),
            "ai_pmpm_abs_diff": float(abs(np.mean(sav_ai) - np.mean(sav_ai_r))),
            "admin_pmpm_savings_run1": float(np.mean(sav_admin)),
            "admin_pmpm_savings_run2": float(np.mean(sav_admin_r)),
            "admin_pmpm_abs_diff": float(abs(np.mean(sav_admin) - np.mean(sav_admin_r))),
            "hosp_reduction_run1": float(sq["hosp_per_1000"].mean() - ai["hosp_per_1000"].mean()),
            "hosp_reduction_run2": float(sq_r["hosp_per_1000"].mean() - ai_r["hosp_per_1000"].mean()),
            "mcse_ai_pmpm_savings": float(np.std(sav_ai, ddof=1) / np.sqrt(N)),
            "mcse_admin_pmpm_savings": float(np.std(sav_admin, ddof=1) / np.sqrt(N)),
        }
        mcs = canonical["monte_carlo_stability"]
        log.info(f"  run-to-run |diff| total ${mcs['ai_pmpm_abs_diff']:.2f}, "
                 f"admin ${mcs['admin_pmpm_abs_diff']:.2f}; MCSE ${mcs['mcse_ai_pmpm_savings']:.2f}")

        # ============================================================
        # 2. WELFARE
        # ============================================================
        log.info("=== 2. Welfare ===")
        summ_rows = []
        for s, d in main_res.items():
            row = {"scenario": s}
            for m in METRICS:
                row[f"{m}_mean"] = d[m].mean()
                row[f"{m}_median"] = d[m].median()
                row[f"{m}_p025"] = d[m].quantile(0.025)
                row[f"{m}_p975"] = d[m].quantile(0.975)
            row["hedis_racial_gap_mean"] = (
                d["hedis_racial_gap"].mean() if "hedis_racial_gap" in d else 0.0
            )
            summ_rows.append(row)
        summ_df = pd.DataFrame(summ_rows)
        if "hedis_racial_gap_mean" not in summ_df:
            summ_df["hedis_racial_gap_mean"] = 0.0
        welfare = compute_welfare(summ_df)
        welfare_zero = compute_welfare(summ_df, transfer_value=0.0)
        wtp = sensitivity_wtp(summ_df)
        wtp_zero = sensitivity_wtp(summ_df, transfer_value=0.0)
        welfare.to_csv(OUT / "welfare.csv", index=False)
        wtp.to_csv(OUT / "wtp_sensitivity.csv", index=False)
        aci = welfare[welfare.scenario == "ai_aco"].iloc[0]

        def _wtp_for(scen, tab=None):
            tab = wtp if tab is None else tab
            return {int(w): float(tab[(tab.scenario == scen) & (tab.wtp_threshold == w)]
                                  ["net_surplus_per_member"].iloc[0])
                    for w in [50000, 100000, 150000, 200000]}

        def _welfare_row(scen, tab):
            r = tab[tab.scenario == scen].iloc[0]
            return {
                "consumer_surplus": float(r["consumer_surplus_per_member"]),
                "consumer_transfer": float(r["consumer_transfer_per_member"]),
                "program_investment": float(r["program_investment_per_member_annual"]),
                "govt_surplus": float(r["govt_surplus_per_member_annual"]),
                "medical_savings": float(r["medical_savings_per_member_annual"]),
                "admin_savings": float(r["admin_savings_per_member_annual"]),
                "producer_surplus": float(r["producer_surplus_per_member"]),
                "producer_transfer": float(r["producer_transfer_per_member"]),
                "net_surplus": float(r["net_surplus_per_member"]),
            }

        canonical["welfare"] = {
            "ai_aco": {
                "consumer_surplus": float(aci["consumer_surplus_per_member"]),
                "consumer_transfer": float(aci["consumer_transfer_per_member"]),
                "program_investment": float(aci["program_investment_per_member_annual"]),
                "govt_surplus": float(aci["govt_surplus_per_member_annual"]),
                "medical_savings": float(aci["medical_savings_per_member_annual"]),
                "admin_savings": float(aci["admin_savings_per_member_annual"]),
                "producer_surplus": float(aci["producer_surplus_per_member"]),
                "producer_transfer": float(aci["producer_transfer_per_member"]),
                "net_surplus": float(aci["net_surplus_per_member"]),
            },
            "wtp": _wtp_for("ai_aco"),
            "wtp_admin_only": _wtp_for("admin_only"),
            "wtp_pessimistic": _wtp_for("ai_aco_pessimistic"),
            "wtp_ffs": _wtp_for("enhanced_ffs"),
            "by_scenario": {s: _welfare_row(s, welfare) for s in MAIN_SCENARIOS if s != "sq_mco"},
            "zero_transfer_bound": {
                "ai_aco": _welfare_row("ai_aco", welfare_zero),
                "wtp": _wtp_for("ai_aco", wtp_zero),
                "wtp_pessimistic": _wtp_for("ai_aco_pessimistic", wtp_zero),
                "aggregate_net_surplus_billions": float(
                    welfare_zero[welfare_zero.scenario == "ai_aco"].iloc[0]["net_surplus_per_member"]
                    * df["PWGTP"].sum() / 1e9),
            },
            "aggregate_net_surplus_billions": float(
                aci["net_surplus_per_member"] * df["PWGTP"].sum() / 1e9
            ),
        }
        log.info(f"  Net social surplus ${aci['net_surplus_per_member']:.0f}/member/yr "
                 f"(CS {aci['consumer_surplus_per_member']:.0f}, "
                 f"GS {aci['govt_surplus_per_member_annual']:.0f}, "
                 f"PS {aci['producer_surplus_per_member']:.0f}); "
                 f"aggregate ${canonical['welfare']['aggregate_net_surplus_billions']:.1f}B")

        # ============================================================
        # 3. DISCOUNT-FACTOR SWEEP (eTable 5) -- d=0 IS the main consensus cell
        # ============================================================
        log.info("=== 3. Discount-factor sweep ===")
        disc_rows = []
        for d_factor in DISCOUNTS:
            aid = eng.cell("ai_aco", N, _spec_discount(d_factor))
            sav = sq["pmpm"].values - aid["pmpm"].values
            gsav = _gross(sq, aid)
            disc_rows.append({
                "discount": d_factor,
                "ai_efficacy_pct": (1 - d_factor) * 100,
                "pmpm_total": float(np.mean(sav)),
                "pmpm_total_gross": float(np.mean(gsav)),
                "program_investment": float(aid["program_investment_pmpm"].mean()),
                "pmpm_p025": float(np.percentile(sav, 2.5)),
                "pmpm_p975": float(np.percentile(sav, 97.5)),
                "pmpm_admin": float(np.mean(sav_admin)),
                "pmpm_clinical_gross": float(np.mean(gsav) - np.mean(sav_admin)),
                "hosp_reduction": float(sq["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
                "ed_reduction": float(sq["ed_per_1000"].mean() - aid["ed_per_1000"].mean()),
                "hedis_improvement": float(
                    (aid["hedis_gap_closure"].mean() - sq["hedis_gap_closure"].mean()) * 100),
                "prob_net_savings": float(np.mean(sav > 0)),
            })
        pd.DataFrame(disc_rows).to_csv(OUT / "discount_sweep.csv", index=False)
        canonical["discount_sweep"] = disc_rows
        log.info(f"  d=0 total ${disc_rows[0]['pmpm_total']:.2f} "
                 f"(admin ${disc_rows[0]['pmpm_admin']:.2f}); "
                 f"d=0.5 total ${disc_rows[-1]['pmpm_total']:.2f}")

        # ============================================================
        # 4. ADMIN-RATE SWEEP (eTable 12)
        # ============================================================
        log.info("=== 4. Admin-rate sweep ===")
        admin_rows = []
        for r in ADMIN_GRID:
            aid = eng.cell("ai_aco", N, {"kind": "ai_admin", "rate": r})
            sav = sq["pmpm"].values - aid["pmpm"].values
            gsav = _gross(sq, aid)
            admin_rows.append({
                "ai_admin_rate": r,
                "pmpm_savings": float(np.mean(sav)),
                "pmpm_savings_gross": float(np.mean(gsav)),
                "prob_gross_savings": float(np.mean(gsav > 0)),
                "pmpm_p025": float(np.percentile(sav, 2.5)),
                "pmpm_p975": float(np.percentile(sav, 97.5)),
                "hosp_reduction": float(sq["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
                "ed_reduction": float(sq["ed_per_1000"].mean() - aid["ed_per_1000"].mean()),
                "prob_net_savings": float(np.mean(sav > 0)),
            })
        pd.DataFrame(admin_rows).to_csv(OUT / "admin_sweep.csv", index=False)
        canonical["admin_sweep"] = admin_rows

        # administrative-only arm across the same grid, for the legal/liability
        # reserve analysis (no assumed AI clinical efficacy)
        admin_only_rows = []
        for r in ADMIN_GRID:
            adr = eng.cell("admin_only", N, {"kind": "ai_admin", "rate": r})
            sav = sq["pmpm"].values - adr["pmpm"].values
            admin_only_rows.append({
                "ai_admin_rate": r,
                "pmpm_savings": float(np.mean(sav)),
                "pmpm_p025": float(np.percentile(sav, 2.5)),
                "pmpm_p975": float(np.percentile(sav, 97.5)),
                "prob_net_savings": float(np.mean(sav > 0)),
            })
        canonical["admin_only_sweep"] = admin_only_rows

        # ============================================================
        # 5. PROVIDER-RATE (eTable 10) + ENCOUNTER SHARE x RATE (eTable 11)
        # ============================================================
        log.info("=== 5. Provider-rate + encounter-share sensitivity ===")
        sq75 = sq  # status quo pays status-quo Medicaid prices; the AI ACO pays the swept rate

        def rate_share(rate, share):
            aid = eng.cell("ai_aco", N, {"kind": "rate_share", "rate": rate,
                                         "share": share, "scale_pcp": False})
            return pd.DataFrame({
                "hosp_red": sq75["hosp_per_1000"].values - aid["hosp_per_1000"].values,
                "ed_red": sq75["ed_per_1000"].values - aid["ed_per_1000"].values,
                "pmpm_sav": sq75["pmpm"].values - aid["pmpm"].values,
                "pmpm_sav_gross": sq75["pmpm_claims"].values - aid["pmpm_claims"].values,
                "hedis_imp": (aid["hedis_gap_closure"].values
                              - sq75["hedis_gap_closure"].values) * 100,
            })

        from microsim.channels import referral_access_factor
        rate_rows = []
        for rate in RATE_GRID:
            d = rate_share(rate, 0.58)
            rate_rows.append({
                "rate": rate,
                "referral_factor": float(referral_access_factor(rate)),
                "hosp_red": float(d["hosp_red"].mean()),
                "hosp_p025": float(d["hosp_red"].quantile(.025)),
                "hosp_p975": float(d["hosp_red"].quantile(.975)),
                "ed_red": float(d["ed_red"].mean()),
                "ed_p025": float(d["ed_red"].quantile(.025)),
                "ed_p975": float(d["ed_red"].quantile(.975)),
                "pmpm_sav": float(d["pmpm_sav"].mean()),
                "pmpm_sav_gross": float(d["pmpm_sav_gross"].mean()),
                "pmpm_p025": float(d["pmpm_sav"].quantile(.025)),
                "pmpm_p975": float(d["pmpm_sav"].quantile(.975)),
                "hedis_imp": float(d["hedis_imp"].mean()),
                "prob_net": float((d["pmpm_sav"] > 0).mean()),
            })
        for rr in rate_rows:
            rr["pct_full_benefit"] = round(100 * rr["hosp_red"] / rate_rows[-1]["hosp_red"])
        canonical["rate_sensitivity"] = rate_rows

        share_rows = []
        for share in SHARE_GRID:
            for rate in [75, 125]:
                d = rate_share(rate, share)
                share_rows.append({
                    "share": share, "rate": rate,
                    "hosp_red": float(d["hosp_red"].mean()),
                    "hedis_imp": float(d["hedis_imp"].mean()),
                    "pmpm_sav": float(d["pmpm_sav"].mean()),
                    "pmpm_sav_gross": float(d["pmpm_sav_gross"].mean()),
                    "prob_net": float((d["pmpm_sav"] > 0).mean()),
                })
        canonical["encounter_share"] = share_rows

        # ============================================================
        # 6. DIGITAL-DIVIDE STRATIFIED (eTable 13)
        # ============================================================
        log.info("=== 6. Digital-divide strata ===")
        strata = sorted(main_res["sq_mco"].iloc[0]["equity_race_metro"].keys())
        dd_rows = []
        sq_recs = main_res["sq_mco"].to_dict("records")
        ai_recs = main_res["ai_aco"].to_dict("records")
        for st in strata:
            def _m(recs, field):
                return float(np.nanmean([r["equity_race_metro"].get(st, {}).get(field, np.nan)
                                         for r in recs]))
            sq_h, ai_h = _m(sq_recs, "hosp_per_1000"), _m(ai_recs, "hosp_per_1000")
            sq_e, ai_e = _m(sq_recs, "engagement_rate"), _m(ai_recs, "engagement_rate")
            dd_rows.append({
                "stratum": st, "sq_hosp": sq_h, "ai_hosp": ai_h,
                "delta_hosp": ai_h - sq_h,
                "sq_eng": sq_e * 100, "ai_eng": ai_e * 100,
                "delta_eng_pp": (ai_e - sq_e) * 100,
            })
        pd.DataFrame(dd_rows).to_csv(OUT / "digital_divide.csv", index=False)
        canonical["digital_divide"] = dd_rows

        race_rows = []
        for race in ["white", "black", "hispanic", "aian"]:
            sq_h = float(np.nanmean([r["equity_by_race"].get(race, {}).get("hosp_per_1000", np.nan)
                                     for r in sq_recs]))
            ai_h = float(np.nanmean([r["equity_by_race"].get(race, {}).get("hosp_per_1000", np.nan)
                                     for r in ai_recs]))
            race_rows.append({"race": race, "sq_hosp": sq_h, "ai_hosp": ai_h,
                              "reduction": sq_h - ai_h})
        canonical["equity_by_race"] = race_rows

        # ============================================================
        # 7. PARAMETER IMPORTANCE (Spearman)
        # ============================================================
        log.info("=== 7. Parameter importance ===")
        from scipy.stats import spearmanr
        inp = pd.DataFrame({
            "admin_diff": [draws[i]["sq_admin_rate"] - draws[i]["ai_admin_rate"] for i in range(N)],
            "base_hosp": [draws[i]["baseline_util"]["rising"]["hosp"] for i in range(N)],
            "eng_mult": [draws[i]["ai_multipliers"]["outreach"]
                         * draws[i]["ai_multipliers"]["agreement"] for i in range(N)],
            "hosp_rr": [draws[i]["ai_rr"]["rising"]["hosp"] for i in range(N)],
            "ed_rr": [draws[i]["ai_rr"]["rising"]["ed"] for i in range(N)],
            "savings": sav_ai,
        })
        canonical["parameter_importance"] = {
            k: float(spearmanr(inp[k], inp["savings"]).statistic)
            for k in ["admin_diff", "base_hosp", "eng_mult", "hosp_rr", "ed_rr"]
        }
        log.info(f"  Spearman admin_diff={canonical['parameter_importance']['admin_diff']:.2f}")

        # ============================================================
        # 8. ADMIN-BASELINE VARIATION ACROSS THE MILLIMAN DISTRIBUTION
        # ============================================================
        log.info("=== 8. Administrative-baseline variation ===")
        state_rows = []
        for label, b in ADMIN_BASELINES.items():
            sqb = eng.cell("sq_mco", N, {"kind": "sq_admin", "rate": b})
            sav = sqb["pmpm"].values - ai["pmpm"].values
            gsav = _gross(sqb, ai)
            state_rows.append({
                "baseline_label": label, "sq_admin": b,
                "pmpm_savings": float(np.mean(sav)),
                "pmpm_savings_gross": float(np.mean(gsav)),
                "pmpm_p025": float(np.percentile(sav, 2.5)),
                "pmpm_p975": float(np.percentile(sav, 97.5)),
                "prob_net": float(np.mean(sav > 0)),
            })
        pd.DataFrame(state_rows).to_csv(OUT / "state_admin_variation.csv", index=False)
        canonical["state_admin_variation"] = state_rows

        # ============================================================
        # 9. PROGRAM-INVESTMENT ACCOUNTING
        # ============================================================
        log.info("=== 9. Program-investment accounting ===")
        chw_pmpm = CHW_PER_1000 * CHW_LOADED_ANNUAL / 1000.0 / 12.0
        tele_pmpm_amort = TELEHEALTH_PER_MEMBER / (TELEHEALTH_AMORT_YEARS * 12.0)
        tele_pmpm_yr1 = TELEHEALTH_PER_MEMBER / 12.0
        gross = float(np.mean(gsav_ai))
        admin_only_sav = float(np.mean(sav_admin))
        invest_steady = chw_pmpm + SOCIAL_PMPM + tele_pmpm_amort
        assert abs(invest_steady - float(ai["program_investment_pmpm"].mean())) < 1e-9
        invest_yr1 = chw_pmpm + SOCIAL_PMPM + tele_pmpm_yr1
        canonical["program_investment"] = {
            "chw_pmpm": chw_pmpm,
            "social_pmpm": SOCIAL_PMPM,
            "telehealth_pmpm_amortized": tele_pmpm_amort,
            "telehealth_pmpm_year1": tele_pmpm_yr1,
            "total_investment_steady": invest_steady,
            "total_investment_year1": invest_yr1,
            "gross_pmpm_savings": gross,
            "net_pmpm_savings_steady": float(np.mean(sav_ai)),
            "net_pmpm_savings_steady_ui": [float(np.percentile(sav_ai, 2.5)),
                                           float(np.percentile(sav_ai, 97.5))],
            "prob_net_savings_steady": float(np.mean(sav_ai > 0)),
            "by_scenario": {s: float(main_res[s]["program_investment_pmpm"].mean())
                            for s in MAIN_SCENARIOS},
            "net_pmpm_savings_year1": gross - invest_yr1,
            "admin_only_savings_no_investment": admin_only_sav,
            "note": ("Program investment is included in modeled payer cost; 'pmpm' is claims "
                     "(medical plus administrative loading) plus investment. Gross savings are "
                     "claims-only. Social-services spending is a transfer to members. The "
                     "administrative-only arm requires no clinical program investment; care "
                     "coordination without AI carries care-management staff only."),
        }
        log.info(f"  gross ${gross:.2f} - invest ${invest_steady:.2f} "
                 f"= net ${gross-invest_steady:.2f} (admin-only ${admin_only_sav:.2f})")

        # ============================================================
        # 10. AI DEPLOYMENT COST -- transparent bounding calculation
        # ============================================================
        log.info("=== 10. AI deployment cost ===")
        ai_interactions_per_member_yr = 6.0

        def ai_cost_pmpm(in_tok, out_tok, price_in, price_out, models=3):
            per_interaction = models * (in_tok / 1e6 * price_in + out_tok / 1e6 * price_out)
            return per_interaction * ai_interactions_per_member_yr / 12.0

        canonical["ai_deployment_cost"] = {
            "assumptions": {"ai_interactions_per_member_yr": ai_interactions_per_member_yr,
                            "ensemble_models": 3,
                            "input_tokens_per_call": 30000,
                            "output_tokens_per_call": 5000},
            "low_pmpm": round(ai_cost_pmpm(30000, 5000, 3.0, 15.0), 2),
            "mid_pmpm": round(ai_cost_pmpm(30000, 5000, 5.0, 15.0), 2),
            "high_pmpm_10x_usage": round(ai_cost_pmpm(30000, 5000, 5.0, 15.0) * 10, 2),
            "note": ("Order $0.3 to $3 PMPM at current commercial API prices; within the "
                     "approximately 3% retained administrative floor even at ten-fold usage."),
        }

        # ============================================================
        # 11. CHW-STAFFING ENGAGEMENT SENSITIVITY
        # ============================================================
        log.info("=== 11. CHW-staffing engagement sensitivity ===")
        chw_rows = []
        for chw, atten, rel in CHW_STAFFING:
            aid = eng.cell("ai_aco", N, _spec_chw(rel, chw))
            sav = sq["pmpm"].values - aid["pmpm"].values
            gsav = _gross(sq, aid)
            chw_rows.append({
                "chw_per_1000": chw, "engagement_attenuation": atten,
                "pmpm_savings": float(np.mean(sav)),
                "pmpm_savings_gross": float(np.mean(gsav)),
                "program_investment": float(aid["program_investment_pmpm"].mean()),
                "hosp_reduction": float(sq["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
                "engagement_ai": float(aid["engagement_rate"].mean() * 100),
                "prob_net": float(np.mean(sav > 0)),
            })
        pd.DataFrame(chw_rows).to_csv(OUT / "chw_staffing.csv", index=False)
        canonical["chw_staffing"] = chw_rows

        # ============================================================
        # 12. NEW: LEGAL / LIABILITY RESERVE SENSITIVITY (Reviewer 2 P3)
        # ============================================================
        log.info("=== 12. Legal/liability reserve sensitivity ===")
        by_rate_full = {round(r["ai_admin_rate"], 5): r for r in admin_rows}
        by_rate_admin = {round(r["ai_admin_rate"], 5): r for r in admin_only_rows}
        legal_rows = []
        for L in LEGAL_RESERVE_PP:
            rate = round(0.030 + L, 5)
            full = by_rate_full[rate]
            adm = by_rate_admin[rate]
            legal_rows.append({
                "legal_reserve_pp_of_premium": L * 100,
                "effective_admin_rate": rate,
                "full_model_pmpm_savings_gross": full["pmpm_savings_gross"],
                "full_model_prob_net_savings": full["prob_net_savings"],
                "full_model_pmpm_net_of_investment": full["pmpm_savings"],
                "admin_only_pmpm_savings": adm["pmpm_savings"],
                "admin_only_prob_net_savings": adm["prob_net_savings"],
            })
        # Break-even: the administrative-only saving is exhausted when the AI ACO
        # administrative rate equals the status-quo baseline.
        sq_base = float(np.mean([d["sq_admin_rate"] for d in draws]))
        legal_breakeven_pp = (sq_base - 0.030) * 100
        canonical["legal_liability_sensitivity"] = {
            "rows": legal_rows,
            "sq_admin_baseline_mean": sq_base,
            "breakeven_reserve_pp_admin_only": legal_breakeven_pp,
            "breakeven_reserve_pmpm_admin_only": admin_only_sav,
            "note": ("A legal or liability reserve is an additional administrative percentage "
                     "point of premium, so its effect is read directly off the administrative-rate "
                     "curve (eTable 12) rather than requiring separate machinery. The plausible "
                     "band is anchored to the 'Other' component of the observed Medicaid MCO "
                     "administrative loss ratio (approximately 0.3% of premium in the lowest "
                     "quartile; eTable 15); the upper end of the sweep (3.0 percentage points) is "
                     "a stress test well above any observed value."),
        }
        log.info(f"  admin-only saving exhausted at a reserve of "
                 f"{legal_breakeven_pp:.1f} pp of premium (${admin_only_sav:.2f} PMPM)")

        # ============================================================
        # 13. NEW: AI-ATTRIBUTABLE VS STRUCTURAL ADMINISTRATIVE DECOMPOSITION
        # ============================================================
        log.info("=== 13. AI-attributable vs structural administrative decomposition ===")
        # Sahni, Stein, Zemmel & Cutler (NBER WP 30857, rev. Oct 2023) estimate that
        # wider AI adoption could reduce private-payer administrative costs by
        # roughly 8% to 14% of that cost category. Applied to the 7.7% baseline
        # this implies an AI-attributable floor of 6.6% to 7.1% of premium.
        greylit = {}
        for tag, frac in [("ai_only_8pct", 0.08), ("ai_only_14pct", 0.14)]:
            rate = round(0.077 * (1 - frac), 5)
            nearest = min(ADMIN_GRID, key=lambda g: abs(g - rate))
            row = by_rate_full[round(nearest, 5)]
            greylit[tag] = {
                "assumed_ai_admin_reduction_pct": frac * 100,
                "implied_admin_rate": rate,
                "grid_rate_used": nearest,
                "pmpm_savings": row["pmpm_savings"],
                "pmpm_savings_gross": row["pmpm_savings_gross"],
                "prob_net_savings": row["prob_net_savings"],
                "admin_only_pmpm_savings": by_rate_admin[round(nearest, 5)]["pmpm_savings"],
                "admin_only_prob_net_savings": by_rate_admin[round(nearest, 5)]["prob_net_savings"],
            }
        canonical["greylit_ai_admin_anchor"] = {
            "source": ("Sahni N, Stein G, Zemmel R, Cutler DM. The potential impact of "
                       "artificial intelligence on healthcare spending. NBER Working Paper "
                       "30857; January 2023, revised October 2023 (private payers: "
                       "administrative-cost reduction of roughly 8% to 14% of that category)."),
            "baseline_alr": 0.077,
            "scenarios": greylit,
        }

        # ============================================================
        # 14. PRICING AND SPILLOVER SENSITIVITY
        # ============================================================
        log.info("=== 14. Pricing and spillover sensitivity ===")
        sens = {}
        for tag, spec in [
            ("hospital_sq_106_supplemental", {"kind": "price", "sq_hosp_rate_pct": 106.0}),
            ("provider_rates_unpriced", {"kind": "price", "price_provider_rates": False}),
            ("no_nonengaged_spillover", {"kind": "spillover", "hosp": 1.0, "ed": 1.0}),
        ]:
            aid = eng.cell("ai_aco", N, spec)
            sav = sq["pmpm"].values - aid["pmpm"].values
            sens[tag] = {
                "pmpm_savings": float(np.mean(sav)),
                "pmpm_p025": float(np.percentile(sav, 2.5)),
                "pmpm_p975": float(np.percentile(sav, 97.5)),
                "prob_net_savings": float(np.mean(sav > 0)),
                "pmpm_savings_gross": float(np.mean(_gross(sq, aid))),
                "hosp_reduction": float(sq["hosp_per_1000"].mean() - aid["hosp_per_1000"].mean()),
                "ed_reduction": float(sq["ed_per_1000"].mean() - aid["ed_per_1000"].mean()),
            }
            log.info(f"  {tag}: net ${sens[tag]['pmpm_savings']:.2f}, hosp {sens[tag]['hosp_reduction']:.1f}")
        canonical["pricing_spillover_sensitivity"] = sens
        # Provider-rate cost component of the full model: gross claims savings
        # with rates unpriced minus gross claims savings with rates priced.
        canonical["provider_rate_cost_pmpm"] = (
            sens["provider_rates_unpriced"]["pmpm_savings_gross"] - float(np.mean(gsav_ai)))
        # Welfare decomposition: administrative component taken from the
        # administrative-reform-only arm so it matches the Results decomposition.
        w = canonical["welfare"]["ai_aco"]
        w["admin_savings"] = float(12 * np.mean(sav_admin))
        w["medical_savings"] = float(w["govt_surplus"] + w["program_investment"] - w["admin_savings"])

        log.info(f"Engine: {eng.n_sims:,} simulations executed, "
                 f"{eng.n_cached:,} cell-reads served from cache")
        canonical["meta"]["simulations_executed"] = int(eng.n_sims)
        canonical["meta"]["cached_cell_reads"] = int(eng.n_cached)

        # ============================================================
        # SAVE
        # ============================================================
        with open(OUT / "canonical_results.json", "w") as f:
            json.dump(canonical, f, indent=2)
        log.info(f"Saved canonical_results.json to {OUT}")

        for s, d in main_res.items():
            d.drop(columns=[c for c in ["equity_by_race", "equity_by_metro", "equity_race_metro"]
                            if c in d], errors="ignore").to_parquet(
                OUT / f"psa_{s}.parquet", index=False)

    log.info(f"Total wall clock {time.time()-t0:.0f}s")
    print("\n===== HEADLINE SUMMARY =====")
    print(json.dumps(canonical["headline"], indent=2))
    print(json.dumps(canonical["monte_carlo_stability"], indent=2))
    print(json.dumps(canonical["program_investment"], indent=2))


if __name__ == "__main__":
    main()
