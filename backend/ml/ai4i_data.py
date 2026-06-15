"""
AI4I 2020 Predictive Maintenance Dataset loader.

Loads the real UCI AI4I 2020 dataset (ai4i_2020_dataset.csv) from the
backend root directory. Falls back to synthetic generation only if the
file is missing — so the model always trains on real data when available.

Dataset: Matzka, S. (2020). Explainable Artificial Intelligence for
Predictive Maintenance Applications. UCI ML Repository.
DOI: 10.1109/AI4I49448.2020.00023
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("Stelos.ML")

# Real dataset lives one level up from this file (backend/ai4i_2020_dataset.csv)
_CSV_PATH = Path(__file__).parent.parent / "ai4i_2020_dataset.csv"

REQUIRED_COLUMNS = [
    "air_temperature", "process_temperature", "rotational_speed",
    "torque", "tool_wear", "temp_diff", "power", "rpm_torque_ratio",
    "machine_failure", "TWF", "HDF", "PWF", "OSF", "RNF",
]


def generate(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Returns the AI4I 2020 dataset.
    Priority: real CSV → synthetic fallback.
    """
    if _CSV_PATH.exists():
        try:
            df = pd.read_csv(_CSV_PATH)
            # Ensure all required columns are present
            missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                raise ValueError(f"CSV missing columns: {missing}")
            df = df[["type"] + REQUIRED_COLUMNS].dropna()
            logger.info(
                f"Loaded REAL AI4I 2020 dataset from {_CSV_PATH.name} "
                f"({len(df):,} rows, {df['machine_failure'].sum()} failures)"
            )
            return df
        except Exception as exc:
            logger.warning(f"Failed to load real CSV ({exc}) — falling back to synthetic data")

    # ── Synthetic fallback (Matzka 2020 paper parameters) ──────────────────
    logger.warning("Real dataset not found — generating synthetic AI4I 2020 data")
    rng = np.random.RandomState(seed)

    types = rng.choice(["L", "M", "H"], size=n_samples, p=[0.60, 0.30, 0.10])

    air_temp   = rng.normal(300.0, 2.0, n_samples)
    proc_temp  = air_temp + rng.normal(10.0, 1.0, n_samples)
    rot_speed  = np.clip(rng.normal(1500, 200, n_samples), 800, 3000).astype(int)
    torque     = np.clip(rng.normal(40.0, 10.0, n_samples), 3.0, 80.0)
    tool_wear  = np.clip(rng.uniform(0, 250, n_samples), 0, 250).astype(int)

    temp_diff        = proc_temp - air_temp
    power            = torque * rot_speed * 2.0 * np.pi / 60.0
    rpm_torque_ratio = rot_speed / np.maximum(torque, 0.1)

    twf_thresh      = rng.randint(200, 241, n_samples)
    twf             = ((tool_wear >= twf_thresh) & (tool_wear <= 250)).astype(int)
    hdf             = ((temp_diff < 8.6) & (rot_speed < 1380)).astype(int)
    pwf             = ((power < 3500) | (power > 9000)).astype(int)
    osf_thresh      = np.where(types == "L", 11000, np.where(types == "M", 12000, 13000))
    osf             = ((torque * tool_wear) > osf_thresh).astype(int)
    rnf             = (rng.uniform(0, 1, n_samples) < 0.001).astype(int)
    machine_failure = np.clip(twf + hdf + pwf + osf + rnf, 0, 1)

    return pd.DataFrame({
        "type":                 types,
        "air_temperature":      air_temp.round(1),
        "process_temperature":  proc_temp.round(1),
        "rotational_speed":     rot_speed,
        "torque":               torque.round(1),
        "tool_wear":            tool_wear,
        "temp_diff":            temp_diff.round(2),
        "power":                power.round(1),
        "rpm_torque_ratio":     rpm_torque_ratio.round(2),
        "machine_failure":      machine_failure,
        "TWF": twf, "HDF": hdf, "PWF": pwf, "OSF": osf, "RNF": rnf,
    })
