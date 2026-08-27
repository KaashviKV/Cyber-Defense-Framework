"""
Random Forest feature importance for dashboard explainability.
"""

from __future__ import annotations

from typing import Any

import joblib

from backend.config.config import RF_MODEL_PATH
from ml.feature_names import FEATURE_NAMES as DEFAULT_FEATURE_NAMES


def get_feature_importance(top_n: int = 5) -> dict[str, Any]:
    if not RF_MODEL_PATH.exists():
        return {
            "status": "error",
            "code": "MODEL_MISSING",
            "message": "Random Forest model not found.",
        }

    model = joblib.load(RF_MODEL_PATH)
    importances = model.feature_importances_

    names = getattr(model, "feature_names_in_", None)
    if names is not None and len(names) == len(importances):
        feature_names = [str(name).strip() for name in names]
    elif len(DEFAULT_FEATURE_NAMES) >= len(importances):
        feature_names = DEFAULT_FEATURE_NAMES[: len(importances)]
    else:
        feature_names = [f"Feature {i + 1}" for i in range(len(importances))]

    ranked = sorted(
        zip(feature_names, importances),
        key=lambda item: item[1],
        reverse=True,
    )[:top_n]

    features = [
        {
            "feature": name,
            "importance": round(float(score) * 100, 2),
        }
        for name, score in ranked
    ]

    return {
        "status": "success",
        "algorithm": "Random Forest",
        "top_features": features,
    }
