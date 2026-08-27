"""
Compare IDS classifiers on CICIDS2017 processed splits.

Reports accuracy, weighted/macro precision-recall-F1, per-class recall,
false positive rate (benign as attack), false negative rate, and training time.

Usage:
  python scripts/compare_ml_models.py
  python scripts/compare_ml_models.py --synthetic   # CI smoke data only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "dataset" / "CICIDS2017" / "processed" / "train_test_data.pkl"
OUT_PATH = PROJECT_ROOT / "ml" / "saved_models" / "ml_model_comparison.json"


def _binary_security_rates(y_true, y_pred, benign_label) -> dict:
    yt = np.array(y_true)
    yp = np.array(y_pred)
    benign = yt == benign_label
    attack = ~benign
    pred_attack = yp != benign_label
    pred_benign = yp == benign_label
    fpr = float(np.mean(pred_attack[benign])) if benign.any() else 0.0
    fnr = float(np.mean(pred_benign[attack])) if attack.any() else 0.0
    detection_rate = float(np.mean(pred_attack[attack])) if attack.any() else 0.0
    return {
        "detection_rate": round(detection_rate, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
    }


def _metrics(y_true, y_pred, train_seconds: float, name: str, benign_label) -> dict:
    labels = np.unique(np.concatenate([np.array(y_true), np.array(y_pred)]))
    per_class = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    return {
        "model": name,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_weighted": round(
            float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4
        ),
        "recall_weighted": round(
            float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4
        ),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "training_seconds": round(train_seconds, 3),
        "per_class_recall": {
            str(label): round(float(score), 4) for label, score in zip(labels, per_class)
        },
        **_binary_security_rates(y_true, y_pred, benign_label),
    }


def _load_data(synthetic: bool, max_train: int, max_test: int):
    if synthetic:
        from sklearn.datasets import make_classification

        x, y = make_classification(
            n_samples=min(4000, max_train + max_test),
            n_features=78,
            n_informative=20,
            n_redundant=10,
            n_classes=8,
            n_clusters_per_class=1,
            random_state=42,
        )
        split = int(0.75 * len(y))
        return x[:split], x[split:], y[:split], y[split:], 0, True

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed CICIDS2017 data not found at {DATA_PATH}. "
            "Run preprocessing first, or pass --synthetic for a smoke test."
        )

    import joblib

    x_train, x_test, y_train, y_test = joblib.load(DATA_PATH)
    x_train = np.asarray(x_train)
    x_test = np.asarray(x_test)
    y_train = np.asarray(y_train)
    y_test = np.asarray(y_test)

    if max_train and len(y_train) > max_train:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(y_train), size=max_train, replace=False)
        x_train, y_train = x_train[idx], y_train[idx]
    if max_test and len(y_test) > max_test:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(y_test), size=max_test, replace=False)
        x_test, y_test = x_test[idx], y_test[idx]

    # Prefer string/int label 0 or "BENIGN"
    unique = list(np.unique(y_train))
    benign = 0 if 0 in unique else unique[0]
    for candidate in ("BENIGN", "Benign", "benign"):
        if candidate in unique:
            benign = candidate
            break
    return x_train, x_test, y_train, y_test, benign, False


def _models(quick: bool):
    n_est = 40 if quick else 100
    return [
        ("Random Forest", RandomForestClassifier(n_estimators=n_est, random_state=42, n_jobs=-1)),
        ("Decision Tree", DecisionTreeClassifier(random_state=42, max_depth=24)),
        (
            "Gradient Boosting",
            GradientBoostingClassifier(random_state=42, n_estimators=40 if quick else 80, max_depth=3),
        ),
        (
            "SVM (LinearSVC)",
            LinearSVC(random_state=42, max_iter=2000, dual="auto"),
        ),
        (
            "Logistic Regression",
            LogisticRegression(max_iter=400, n_jobs=-1, random_state=42),
        ),
        (
            "MLP (neural baseline)",
            MLPClassifier(
                hidden_layer_sizes=(64,) if quick else (128, 64),
                max_iter=12 if quick else 25,
                random_state=42,
            ),
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--max-train", type=int, default=25000)
    parser.add_argument("--max-test", type=int, default=8000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    x_train, x_test, y_train, y_test, benign, synthetic = _load_data(
        args.synthetic, args.max_train, args.max_test
    )

    try:
        from xgboost import XGBClassifier

        extras = [("XGBoost", XGBClassifier(n_estimators=80, max_depth=6, n_jobs=-1, random_state=42, eval_metric="mlogloss"))]
    except Exception:
        extras = []

    rows = []
    for name, model in _models(args.quick) + extras:
        print(f"Training {name}...", flush=True)
        start = time.perf_counter()
        try:
            model.fit(x_train, y_train)
        except Exception as exc:
            rows.append({"model": name, "error": str(exc)})
            continue
        elapsed = time.perf_counter() - start
        pred = model.predict(x_test)
        row = _metrics(y_test, pred, elapsed, name, benign)
        rows.append(row)
        print(
            f"  acc={row['accuracy']:.4f} macro-F1={row['macro_f1']:.4f} "
            f"FPR={row['false_positive_rate']:.4f} train={row['training_seconds']}s"
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "synthetic_smoke" if synthetic else "CICIDS2017",
        "train_samples": int(len(y_train)),
        "test_samples": int(len(y_test)),
        "note": (
            "Use macro-F1 and per-class recall for imbalanced CICIDS2017 classes. "
            "Detection/FPR/FNR treat BENIGN vs all attacks."
        ),
        "results": rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== IDS Model Comparison ===")
    print(f"{'Model':<24} {'Acc':>7} {'MacroF1':>8} {'FPR':>8} {'FNR':>8} {'Train(s)':>9}")
    for row in rows:
        if "error" in row:
            print(f"{row['model']:<24} ERROR {row['error']}")
            continue
        print(
            f"{row['model']:<24} {row['accuracy']:>7.4f} {row['macro_f1']:>8.4f} "
            f"{row['false_positive_rate']:>8.4f} {row['false_negative_rate']:>8.4f} "
            f"{row['training_seconds']:>9.2f}"
        )
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
