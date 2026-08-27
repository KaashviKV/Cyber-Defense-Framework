"""
Evaluate the trained Random Forest model on held-out test data.
"""

from __future__ import annotations

import os
from typing import Any

import joblib
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "dataset",
    "CICIDS2017",
    "processed",
    "train_test_data.pkl",
)

MODEL_PATH = os.path.join(
    CURRENT_DIR,
    "saved_models",
    "random_forest_model.pkl",
)


def get_model_performance_metrics() -> dict[str, Any]:
    """
    Compute Random Forest evaluation metrics on held-out test data.
    Raises FileNotFoundError when model or test data is unavailable.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Test data not found at {DATA_PATH}. "
            "Run preprocessing and feature engineering first."
        )

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run train_model.py first."
        )

    _, x_test, _, y_test = joblib.load(DATA_PATH)
    model = joblib.load(MODEL_PATH)
    y_pred = model.predict(x_test)

    labels = getattr(model, "classes_", None)
    y_test_arr = y_test if hasattr(y_test, "__len__") else y_test
    benign = 0
    unique = set(int(v) if str(v).isdigit() else v for v in (labels if labels is not None else []))
    try:
        unique_test = list(set(y_test.tolist() if hasattr(y_test, "tolist") else list(y_test)))
    except TypeError:
        unique_test = []
    for candidate in (0, "BENIGN", "Benign"):
        if candidate in unique_test or candidate in unique:
            benign = candidate
            break

    yt = y_test_arr
    try:
        import numpy as np

        yt_np = np.asarray(y_test)
        yp_np = np.asarray(y_pred)
        attack = yt_np != benign
        benign_mask = yt_np == benign
        pred_attack = yp_np != benign
        detection_rate = float(np.mean(pred_attack[attack])) if attack.any() else 0.0
        fpr = float(np.mean(pred_attack[benign_mask])) if benign_mask.any() else 0.0
        fnr = float(np.mean(~pred_attack[attack])) if attack.any() else 0.0
    except Exception:
        detection_rate = 0.0
        fpr = 0.0
        fnr = 0.0

    return {
        "algorithm": "Random Forest",
        "dataset": "CICIDS2017",
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(
            float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
            4,
        ),
        "recall": round(
            float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
            4,
        ),
        "f1_score": round(
            float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            4,
        ),
        "macro_f1": round(
            float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
            4,
        ),
        "detection_rate": round(detection_rate, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "test_samples": int(len(y_test)),
    }


def evaluate() -> dict[str, Any]:
    metrics = get_model_performance_metrics()

    print("\n==============================")
    print("MODEL EVALUATION")
    print("==============================")
    for key in ("accuracy", "precision", "recall", "f1_score"):
        print(f"{key.capitalize():10}: {metrics[key]}")

    _, x_test, _, y_test = joblib.load(DATA_PATH)
    model = joblib.load(MODEL_PATH)
    y_pred = model.predict(x_test)

    print("\nClassification Report:\n")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("\nConfusion Matrix:\n")
    print(confusion_matrix(y_test, y_pred))

    return metrics


if __name__ == "__main__":
    evaluate()
