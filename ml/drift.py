"""Population Stability Index vs an optional training-feature reference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

REFERENCE_PATH = Path(__file__).resolve().parent / "saved_models" / "drift_reference.json"


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if expected.size == 0 or actual.size == 0:
        return 0.0
    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.unique(np.quantile(expected, quantiles))
    if len(edges) < 3:
        return 0.0
    e_counts, _ = np.histogram(expected, bins=edges)
    a_counts, _ = np.histogram(actual, bins=edges)
    e_prop = np.clip(e_counts / max(e_counts.sum(), 1), 1e-6, 1)
    a_prop = np.clip(a_counts / max(a_counts.sum(), 1), 1e-6, 1)
    return float(np.sum((a_prop - e_prop) * np.log(a_prop / e_prop)))


def evaluate_vector(features) -> dict[str, Any]:
    if not REFERENCE_PATH.exists():
        return {
            "status": "unconfigured",
            "message": "No drift_reference.json. Run scripts/build_drift_reference.py when CICIDS data is available.",
            "psi": None,
            "level": "UNKNOWN",
        }
    try:
        with open(REFERENCE_PATH, encoding="utf-8") as fh:
            ref = json.load(fh)
        means = np.asarray(ref.get("feature_means") or [], dtype=float)
        vector = np.asarray(features, dtype=float).reshape(-1)
        if means.size == 0 or vector.size == 0:
            return {"status": "unconfigured", "psi": None, "level": "UNKNOWN"}
        n = min(len(means), len(vector))
        delta = float(np.mean(np.abs(vector[:n] - means[:n])))
        psi = round(min(2.0, delta / (np.mean(np.abs(means[:n])) + 1e-6)), 4)
        if psi < 0.1:
            level = "LOW"
        elif psi < 0.25:
            level = "MODERATE"
        else:
            level = "HIGH"
        return {"status": "ok", "psi": psi, "level": level, "ood_hint": psi >= 0.25}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "psi": None, "level": "UNKNOWN"}
