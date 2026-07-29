"""
Random Forest feature importance for dashboard explainability.
"""

from __future__ import annotations

from typing import Any

import joblib

from backend.config.config import RF_MODEL_PATH

# Common CICIDS2017-style feature names (fallback when model has no names)
DEFAULT_FEATURE_NAMES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Packets Fwd Min",
    "Packets Fwd Max",
    "Packets Fwd Mean",
    "Packets Fwd Std",
    "Packets Bwd Min",
    "Packets Bwd Max",
    "Packets Bwd Mean",
    "Packets Bwd Std",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "CWE Flag Count",
    "ECE Flag Count",
    "Down/Up Ratio",
    "Avg Packet Size",
    "Avg Fwd Segment Size",
    "Avg Bwd Segment Size",
    "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk",
    "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    "Init Win Bytes Fwd",
    "Init Win Bytes Bwd",
    "Act Data Pkts Fwd",
    "Min Seg Size Fwd",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
]


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
