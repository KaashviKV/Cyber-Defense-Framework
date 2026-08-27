"""Shared helpers for research dataset adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_root() -> Path:
    return PROJECT_ROOT


def drop_identifier_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove index / Unnamed / id columns that are not predictive features."""
    drop_cols: list[str] = []
    for col in df.columns:
        name = str(col).strip()
        lower = name.lower()
        if lower in {"id", "index"} or name.startswith("Unnamed"):
            drop_cols.append(col)
    if drop_cols:
        return df.drop(columns=drop_cols)
    return df


def replace_non_finite(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Replace ±inf with NaN so imputers can handle them."""
    out = df.copy()
    cols = [c for c in columns if c in out.columns]
    if not cols:
        return out
    values = out[cols].to_numpy(dtype=float, copy=True)
    values[~np.isfinite(values)] = np.nan
    out[cols] = values
    return out


def class_distribution(series: pd.Series) -> dict[str, int]:
    counts = series.astype(str).value_counts(dropna=False)
    return {str(k): int(v) for k, v in counts.items()}
