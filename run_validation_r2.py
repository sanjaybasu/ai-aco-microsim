#!/usr/bin/env python3
"""Revision-2 reform-reproduction check (eTable 8, Figure 2).

Re-runs microsim.validation backtests with the scipy global RNG seeded per reform
(the PSA parameter sampler draws from it), and records the reform-specific
parameters exactly as coded, so eTable 8 is generated from the code rather than
typed. Output: output/revision2/validation_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from microsim.population import load_population  # noqa: E402
from microsim.parameters import AIACOPSAParameters  # noqa: E402
from microsim import validation as V  # noqa: E402
import functools  # noqa: E402

# Use the revision-2 sampler settings (untruncated admin rates, racial engagement
# penalties sampled) for the reform-reproduction check as well.
AIACOPSAParameters.sample = functools.partialmethod(
    AIACOPSAParameters.sample, clip_admin=False, sample_racial_penalty=True)

POP = str(ROOT / "data" / "acs_pums_medicaid_adults_hins4.parquet")  # Medicaid (HINS4) adults 19-64
OUT = ROOT / "output" / "revision2"
SEED, N = 42, 200
REFORMS = ["oregon_cco", "medicare_pioneer_aco", "chw_impact", "mssp", "cpc_plus"]

df = load_population(cache_path=POP)
np.random.seed(SEED)
base = AIACOPSAParameters().sample()  # partialmethod applies R2 settings
params = {}
for r in REFORMS:
    p = V._make_backtest_params(base, r)
    params[r] = {
        "multipliers": p["ai_multipliers"],
        "rr": {t: p["ai_rr"][t] for t in ["low", "rising", "high"]},
        "spillover_hosp": p.get("spillover_hosp", 0.97),
        "spillover_ed": p.get("spillover_ed", 0.98),
        "admin_factor_vs_sq": round(p["ai_admin_rate"] / p["sq_admin_rate"], 4),
        "cost_reduction_engaged": p.get("cost_reduction_engaged", 1.0),
        "pcp_increase": p["ai_pcp_increase"],
    }

results = []
for r in REFORMS:
    np.random.seed(SEED)
    res = V.run_backtest(df, r, N, SEED)
    for m in res["metrics"].values():
        m["simulated_95ui"] = list(m["simulated_95ui"])
        m["observed_95ci"] = list(m["observed_95ci"])
        m["coverage"] = bool(m["coverage"]) if m["coverage"] is not None else None
    results.append(res)
agg = V.compute_aggregate_metrics(results)
json.dump({"seed": SEED, "n_iterations": N, "parameters": params, "results": results,
           "aggregate": {k: float(v) for k, v in agg.items()}},
          open(OUT / "validation_results.json", "w"), indent=2, default=float)
print(json.dumps(agg, indent=2, default=float))
