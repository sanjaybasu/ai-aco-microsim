#!/usr/bin/env python3
"""Build the ACS PUMS Medicaid adult cohort for the AI-ACO microsimulation.

Medicaid coverage in ACS PUMS is HINS4 ("Medicaid, Medical Assistance, or any
kind of government-assistance plan for those with low incomes or a
disability"); HINS3 is Medicare. This script reuses the download, race
classification and metro lookup of medicaid-frailty-bias/data/acs_pums.py and
filters on HINS4 == 1, ages 19-64, excluding Puerto Rico. Source: ACS 2022
1-Year PUMS national person file. Output (data stays local, never committed):
acs_pums_medicaid_adults_hins4.parquet in this directory.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FB = Path("/Users/sanjaybasu/waymark-local/packaging/medicaid-frailty-bias/data")
sys.path.insert(0, str(FB.parent))
import data.acs_pums as A  # noqa: E402

OUT = HERE / "acs_pums_medicaid_adults_hins4.parquet"
A.PUMS_COLS = A.PUMS_COLS + ["HINS4"]
_orig_filter = A._filter_medicaid_adults


def _filter_hins4(df):
    # route the existing filter through HINS4 by aliasing it onto the column it reads
    df = df.copy()
    df["HINS3_MEDICARE"] = df["HINS3"]
    df["HINS3"] = df["HINS4"]
    out = _orig_filter(df)
    out["HINS4"] = out["HINS3"]
    out["HINS3"] = out["HINS3_MEDICARE"]
    return out.drop(columns=["HINS3_MEDICARE"])


A._filter_medicaid_adults = _filter_hins4
A.CACHE_FILE = OUT
df = A.load_raw_pums(force_download=True)
print(f"Medicaid (HINS4) adults 19-64: {len(df):,}; weighted {df['PWGTP'].sum():,.0f}; "
      f"states {df['state'].nunique()}; mean age {df['AGEP'].mean():.1f}; "
      f"any disability {(df['DIS'] == 1).mean():.3f}; also Medicare {(df['HINS3'] == 1).mean():.3f}")
