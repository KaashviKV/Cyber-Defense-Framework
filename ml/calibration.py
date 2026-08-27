"""Optional probability calibration. Missing artifact → raw RF probabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
CALIBRATOR_PATH = CURRENT_DIR / "saved_models" / "rf_calibrator.pkl"
ECE_PATH = CURRENT_DIR / "saved_models" / "calibration_metrics.json"

_calibrator = None
_loaded = False


def _load():
    global _calibrator, _loaded
    if _loaded:
        return
    _loaded = True
    if not CALIBRATOR_PATH.exists():
        return
    try:
        import joblib

        _calibrator = joblib.load(CALIBRATOR_PATH)
    except Exception:
        _calibrator = None


def enrich_confidence(features: np.ndarray, raw_proba: np.ndarray) -> dict[str, Any]:
    _load()
    raw_max = float(np.max(raw_proba))
    calibrated_max = raw_max
    method = "raw_rf"
    if _calibrator is not None:
        try:
            cal = _calibrator.predict_proba(np.asarray(features, dtype=float).reshape(1, -1))[0]
            calibrated_max = float(np.max(cal))
            method = "platt_or_isotonic"
        except Exception:
            calibrated_max = raw_max
            method = "raw_rf_fallback"

    uncertainty = round(1.0 - calibrated_max, 4)
    if uncertainty < 0.15:
        band = "HIGH"
    elif uncertainty < 0.35:
        band = "MEDIUM"
    else:
        band = "LOW"

    ece = None
    if ECE_PATH.exists():
        try:
            import json

            with open(ECE_PATH, encoding="utf-8") as fh:
                ece = json.load(fh).get("ece")
        except Exception:
            ece = None

    return {
        "raw_confidence": round(raw_max * 100, 2),
        "calibrated_confidence": round(calibrated_max * 100, 2),
        "uncertainty": uncertainty,
        "calibration_confidence_band": band,
        "calibration_method": method,
        "ece": ece,
        "calibrator_loaded": _calibrator is not None,
    }
