#!/usr/bin/env python3
"""
Parallel, memoised evaluation engine for the revision-1 pipeline.

Why this exists
---------------
The revision-1 analysis is a *paired* probabilistic sensitivity analysis (PSA):
for iteration i, every scenario is simulated from the same parameter draw
``draws[i]`` and the same per-iteration event RNG ``default_rng(SEED + i)``, so
that scenario differences reflect the intervention rather than Monte Carlo
noise.  That design has two consequences this module exploits:

1. A given (scenario, parameter-override) cell is a pure function of ``i``.
   It can therefore be evaluated in any order, in any process, and memoised.
   Results are bit-identical to a serial run.
2. Many sweep cells are *identical* to cells already computed (for example the
   status-quo arm does not change across the discount-factor sweep, and the
   AI arm does not change across the status-quo administrative-baseline sweep).
   Memoisation removes that redundant work, which is what makes it affordable
   to raise the iteration count for every sweep to the main-analysis count.

Raising all sweeps to the main iteration count is the point: it makes each
sweep's base-case cell the *same cell* as the main analysis, so base-case rows
in eTable 5, eTable 12, eTable 18 and eTable 20 reproduce Table 1 exactly
rather than approximately.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

_G: Dict[str, Any] = {}


# ---------------------------------------------------------------- worker side
def _init_worker(pop_path: str, draw_sets: Dict[str, List[dict]], seeds: Dict[str, int]):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from microsim.population import load_population  # noqa: WPS433
    _G["df"] = load_population(cache_path=pop_path)
    _G["draws"] = draw_sets
    _G["seeds"] = seeds


def apply_override(base: dict, spec: Optional[dict]) -> dict:
    """Return the parameter dict actually simulated for an override spec.

    ``spec`` of ``None`` or ``{}`` means "simulate the base draw unmodified",
    which is what makes a sweep's base-case cell identical to the main
    analysis cell rather than merely numerically close to it.
    """
    p = dict(base)
    if not spec:
        return p
    kind = spec["kind"]
    if kind == "discount":
        d = spec["d"]
        p["ai_multipliers"] = {k: 1 + (v - 1) * (1 - d) for k, v in base["ai_multipliers"].items()}
        p["ai_rr"] = {t: {k: v * (1 - d) for k, v in base["ai_rr"][t].items()} for t in base["ai_rr"]}
    elif kind == "ai_admin":
        p["ai_admin_rate"] = spec["rate"]
    elif kind == "sq_admin":
        p["sq_admin_rate"] = spec["rate"]
    elif kind == "rate_share":
        p["provider_rate_pct_medicare"] = spec["rate"]
        if spec.get("share") is not None:
            p["ai_encounter_share"] = spec["share"]
        if spec.get("scale_pcp"):
            p["costs"] = dict(base["costs"])
            p["costs"]["pcp"] = base["costs"]["pcp"] * spec["rate"] / 125.0
    elif kind == "chw":
        a = spec["atten"]
        p["ai_multipliers"] = {k: 1 + (v - 1) * (1 - a) for k, v in base["ai_multipliers"].items()}
        if spec.get("per_1000") is not None and "program_investment" in base:
            p["program_investment"] = dict(base["program_investment"])
            p["program_investment"]["chw_pmpm"] = (
                spec["per_1000"] * base["program_investment"]["chw_loaded_annual"] / 1000.0 / 12.0)
    elif kind == "spillover":
        p["spillover_hosp"], p["spillover_ed"] = spec["hosp"], spec["ed"]
    elif kind == "price":
        for k in ("price_provider_rates", "sq_hosp_rate_pct", "sq_pcp_rate_pct", "ai_hosp_rate_pct"):
            if k in spec:
                p[k] = spec[k]
    else:
        raise ValueError(f"unknown override kind: {kind}")
    return p


def scenario_params(sim_scen: str, params: dict) -> dict:
    """Scenario-specific parameters for revision 2 (draws carrying ``r2_scenarios``).

    Minority-report scenarios scale the sampled consensus draws so that their
    means equal the stated values: S2 (optimistic) 1.3x outreach, 1.4x agreement
    and a 2.5% administrative rate; S3 (pessimistic) 1.1x outreach and 1.2x
    agreement (consensus means 1.2x, 1.3x, 3.0%). Clinical relative-risk scaling
    for S2/S3 stays in microsim.channels.
    """
    if not params.get("r2_scenarios") or sim_scen not in ("ai_aco_optimistic", "ai_aco_pessimistic"):
        return params
    p = dict(params)
    m = dict(params["ai_multipliers"])
    if sim_scen == "ai_aco_optimistic":
        m["outreach"] = 1 + (m["outreach"] - 1) * (0.3 / 0.2)
        m["agreement"] = 1 + (m["agreement"] - 1) * (0.4 / 0.3)
        p["ai_admin_rate"] = params["ai_admin_rate"] * (2.5 / 3.0)
    else:
        m["outreach"] = 1 + (m["outreach"] - 1) * (0.1 / 0.2)
        m["agreement"] = 1 + (m["agreement"] - 1) * (0.2 / 0.3)
    p["ai_multipliers"] = m
    return p


# Scenarios that run the full clinical-coordination program (community health
# workers, social-services budget, telehealth capitalization).
CLINICAL_PROGRAM_SCENARIOS = ("ai_aco", "ai_aco_optimistic", "ai_aco_pessimistic", "ai_aco_universal")


def program_investment_pmpm(scenario: str, params: dict) -> Dict[str, float]:
    """Incremental program investment the scenario commits to, per member per month.

    The clinical-coordination scenarios carry community health workers, the
    social-services budget and amortized telehealth. Care coordination without AI
    (enhanced_ffs) carries care-management staff at the same staffing ratio but no
    social-services budget or telehealth. The status quo and the
    administrative-reform-only arm carry none. A draw without a
    ``program_investment`` entry returns zero, which keeps earlier pipelines
    unchanged.
    """
    pi = params.get("program_investment")
    out = {"total": 0.0, "social": 0.0}
    if not pi:
        return out
    if scenario in CLINICAL_PROGRAM_SCENARIOS:
        out["total"] = pi["chw_pmpm"] + pi["social_pmpm"] + pi["telehealth_pmpm"]
        out["social"] = pi["social_pmpm"]
    elif scenario == "enhanced_ffs":
        out["total"] = pi["chw_pmpm"]
    return out


def _job(args):
    draw_set, i, sim_scen, spec = args
    from microsim.channels import simulate_scenario  # noqa: WPS433
    rng = np.random.default_rng(_G["seeds"][draw_set] + i)
    params = scenario_params(sim_scen, apply_override(_G["draws"][draw_set][i], spec))
    r = simulate_scenario(_G["df"], params, sim_scen, rng)
    # Total payer cost = claims (medical + administrative loading) + program
    # investment. "pmpm" is the total, so every downstream saving is net.
    inv = program_investment_pmpm(sim_scen, params)
    r["pmpm_claims"] = r["pmpm"]
    r["program_investment_pmpm"] = inv["total"]
    r["social_transfer_pmpm"] = inv["social"]
    r["pmpm"] = r["pmpm"] + inv["total"]
    r["iteration"] = i
    return r


# ---------------------------------------------------------------- parent side
class Engine:
    """Memoised parallel evaluator for (draw_set, scenario, override) cells."""

    def __init__(self, pop_path: str, draw_sets: Dict[str, List[dict]],
                 seeds: Dict[str, int], workers: Optional[int] = None):
        self._cache: Dict[tuple, pd.DataFrame] = {}
        self.n_sims = 0
        self.n_cached = 0
        self._workers = workers or max(1, (os.cpu_count() or 2) - 2)
        self._ex = ProcessPoolExecutor(
            max_workers=self._workers,
            initializer=_init_worker,
            initargs=(pop_path, draw_sets, seeds),
        )

    def close(self):
        self._ex.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @staticmethod
    def _key(draw_set: str, sim_scen: str, spec: Optional[dict]) -> tuple:
        return (draw_set, sim_scen, json.dumps(spec or {}, sort_keys=True))

    def cell(self, sim_scen: str, n: int, spec: Optional[dict] = None,
             draw_set: str = "main") -> pd.DataFrame:
        """Return a DataFrame with one row per iteration for this cell."""
        key = self._key(draw_set, sim_scen, spec)
        hit = self._cache.get(key)
        if hit is not None and len(hit) >= n:
            self.n_cached += n
            return hit.iloc[:n].reset_index(drop=True)
        jobs = [(draw_set, i, sim_scen, spec) for i in range(n)]
        rows = list(self._ex.map(_job, jobs, chunksize=8))
        self.n_sims += len(jobs)
        out = pd.DataFrame(rows)
        self._cache[key] = out
        return out
