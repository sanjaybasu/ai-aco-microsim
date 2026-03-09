"""
Population Loader for AI ACO Microsimulation
=============================================
Loads ACS PUMS Medicaid adults and extends with digital access
and language variables needed for the 5-channel simulation.

Reuses the acs_pums.py loader from the frailty bias analysis.
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to cached ACS PUMS data from frailty bias analysis
FRAILTY_DATA_PATH = Path(__file__).parent.parent.parent / "medicaid-frailty-bias" / "data"
CACHED_PARQUET = FRAILTY_DATA_PATH / "acs_pums_medicaid_adults.parquet"


def load_population(cache_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load ACS PUMS Medicaid adult population.

    If the frailty bias cached parquet exists, load it and extend.
    Otherwise, create a synthetic population for testing.

    Returns:
        DataFrame with columns: race_eth, metro_status, PWGTP,
        disability domains, digital_access, lep, state, etc.
    """
    path = Path(cache_path) if cache_path else CACHED_PARQUET

    if path.exists():
        logger.info(f"Loading ACS PUMS from {path}")
        df = pd.read_parquet(path)
        df = _standardize_columns(df)
        df = _add_digital_access(df)
        df = _add_language_proxy(df)
        logger.info(f"Loaded {len(df)} individuals from {df['state'].nunique()} states")
        return df
    else:
        logger.warning(f"ACS PUMS cache not found at {path}. Creating synthetic population.")
        return _create_synthetic_population()


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure standard column names exist."""
    # race_eth should already exist from frailty bias processing
    if "race_eth" not in df.columns:
        if "RAC1P" in df.columns:
            race_map = {1: "white", 2: "black", 6: "asian", 7: "aian"}
            hisp_col = "HISP" if "HISP" in df.columns else None
            df["race_eth"] = df["RAC1P"].map(race_map).fillna("other")
            if hisp_col and hisp_col in df.columns:
                df.loc[df[hisp_col] > 1, "race_eth"] = "hispanic"

    # metro_status
    if "metro_status" not in df.columns:
        if "MET2013" in df.columns:
            df["metro_status"] = np.where(df["MET2013"] > 0, "metro", "nonmetro")
        else:
            df["metro_status"] = "metro"  # default

    # state
    if "state" not in df.columns:
        if "ST" in df.columns:
            # Map FIPS to state abbreviation
            fips_to_abbr = {
                5: "AR", 4: "AZ", 13: "GA", 18: "IN", 21: "KY",
                22: "LA", 23: "ME", 26: "MI", 30: "MT", 33: "NH",
                35: "NM", 39: "OH", 45: "SC", 46: "SD", 49: "UT",
                51: "VA", 55: "WI",
            }
            df["state"] = df["ST"].map(fips_to_abbr)
            df = df.dropna(subset=["state"])

    return df


def _add_digital_access(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add digital access proxy variable.

    If ACCESSINET exists in ACS data, use it directly.
    Otherwise, impute from race × metro using FCC broadband data.
    """
    if "ACCESSINET" in df.columns:
        df["has_broadband"] = df["ACCESSINET"].isin([1, 2])  # yes or yes with subscription
    else:
        # Impute from published broadband penetration rates
        broadband_rates = {
            ("white", "metro"): 0.87,
            ("white", "nonmetro"): 0.74,
            ("black", "metro"): 0.80,
            ("black", "nonmetro"): 0.64,
            ("hispanic", "metro"): 0.76,
            ("hispanic", "nonmetro"): 0.60,
            ("aian", "metro"): 0.70,
            ("aian", "nonmetro"): 0.47,
            ("asian", "metro"): 0.90,
            ("asian", "nonmetro"): 0.75,
            ("other", "metro"): 0.80,
            ("other", "nonmetro"): 0.65,
        }
        rng = np.random.default_rng(42)
        probs = df.apply(
            lambda r: broadband_rates.get((r["race_eth"], r["metro_status"]), 0.75),
            axis=1,
        )
        df["has_broadband"] = rng.random(len(df)) < probs.values

    return df


def _add_language_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add limited English proficiency (LEP) proxy.

    If LANX/ENG exists in ACS data, use directly.
    Otherwise, impute from race/ethnicity using ACS language data.
    """
    if "ENG" in df.columns:
        # ENG: 1=very well, 2=well, 3=not well, 4=not at all
        df["lep"] = df["ENG"].isin([3, 4])
    elif "LANX" in df.columns:
        # LANX: 1=speaks only English, 2=speaks another language
        df["lep"] = df["LANX"] == 2
    else:
        lep_rates = {
            "white": 0.04, "black": 0.07, "hispanic": 0.40,
            "asian": 0.30, "aian": 0.12, "other": 0.15,
        }
        rng = np.random.default_rng(43)
        probs = df["race_eth"].map(lep_rates).fillna(0.10)
        df["lep"] = rng.random(len(df)) < probs.values

    return df


def _create_synthetic_population(n: int = 10000) -> pd.DataFrame:
    """Create synthetic population for testing when ACS data unavailable."""
    rng = np.random.default_rng(42)

    races = rng.choice(
        ["white", "black", "hispanic", "aian", "asian", "other"],
        size=n,
        p=[0.40, 0.25, 0.20, 0.05, 0.05, 0.05],
    )
    metros = rng.choice(["metro", "nonmetro"], size=n, p=[0.75, 0.25])
    states = rng.choice(
        ["OH", "VA", "MI", "GA", "IN", "KY", "LA", "AZ"],
        size=n,
    )

    df = pd.DataFrame({
        "race_eth": races,
        "metro_status": metros,
        "state": states,
        "PWGTP": rng.integers(1, 50, size=n),
        "DPHY_bin": rng.choice([0, 1], size=n, p=[0.85, 0.15]),
        "DREM_bin": rng.choice([0, 1], size=n, p=[0.90, 0.10]),
        "DDRS_bin": rng.choice([0, 1], size=n, p=[0.92, 0.08]),
        "DOUT_bin": rng.choice([0, 1], size=n, p=[0.93, 0.07]),
    })

    df = _add_digital_access(df)
    df = _add_language_proxy(df)

    return df
