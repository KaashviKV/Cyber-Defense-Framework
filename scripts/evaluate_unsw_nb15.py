"""
Standalone UNSW-NB15 IDS evaluation (train→test on official splits).

Does NOT touch the production CICIDS2017 Random Forest or /analyze contract.
This is NOT cross-dataset generalization.

Usage:
  python scripts/evaluate_unsw_nb15.py
  python scripts/evaluate_unsw_nb15.py --quick   # subsample for smoke runs
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.common import class_distribution  # noqa: E402
from ml.datasets.unsw_nb15 import (  # noqa: E402
    UNSW_BENIGN_LABEL,
    build_preprocess_pipeline,
    describe_splits,
    load_unsw_nb15_splits,
)

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_evaluation.json"
OUT_MODEL = PROJECT_ROOT / "ml" / "saved_models" / "random_forest_unsw_nb15.pkl"


def _binary_security_metrics(y_true, y_pred, benign_label: str = UNSW_BENIGN_LABEL) -> dict:
    """
    Collapse multiclass predictions to Normal vs attack.

    TP = attack → attack, TN = benign → benign,
    FP = benign → attack, FN = attack → benign.
    """
    yt = np.asarray(y_true).astype(str)
    yp = np.asarray(y_pred).astype(str)
    true_benign = yt == benign_label
    true_attack = ~true_benign
    pred_benign = yp == benign_label
    pred_attack = ~pred_benign

    tp = int(np.sum(true_attack & pred_attack))
    tn = int(np.sum(true_benign & pred_benign))
    fp = int(np.sum(true_benign & pred_attack))
    fn = int(np.sum(true_attack & pred_benign))

    attack_recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0

    return {
        "attack_recall": round(float(attack_recall), 4),
        "detection_rate": round(float(attack_recall), 4),
        "false_positive_rate": round(float(fpr), 4),
        "false_negative_rate": round(float(fnr), 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def _maybe_subsample(x, y, max_rows: int | None, seed: int):
    if not max_rows or len(y) <= max_rows:
        return x, y
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(y), size=max_rows, replace=False)
    return x.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="UNSW-NB15 standalone RF evaluation")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Subsample train/test for a faster smoke run (not for the report).",
    )
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="RF trees (default 100 to match production RF; use 300 for heavier runs).",
    )
    parser.add_argument("--no-save-model", action="store_true")
    args = parser.parse_args()

    max_train = args.max_train if args.max_train is not None else (8000 if args.quick else None)
    max_test = args.max_test if args.max_test is not None else (3000 if args.quick else None)

    print("Loading UNSW-NB15 official train/test splits...", flush=True)
    splits = load_unsw_nb15_splits(PROJECT_ROOT)
    info = describe_splits(splits)

    x_train, y_train = splits.x_train, splits.y_train
    x_test, y_test = splits.x_test, splits.y_test
    x_train, y_train = _maybe_subsample(x_train, y_train, max_train, seed=42)
    x_test, y_test = _maybe_subsample(x_test, y_test, max_test, seed=0)

    print(f"  dataset_dir: {info['dataset_dir']}")
    print(f"  training shape: {x_train.shape}")
    print(f"  testing shape:  {x_test.shape}")
    print(f"  feature_count:  {info['feature_count']}")
    print(f"  numeric:        {info['numeric_feature_count']}")
    print(f"  categorical:    {info['categorical_feature_count']} -> {info['categorical_features']}")
    print(f"  train class distribution: {info['train_class_distribution']}")
    print(f"  test class distribution:  {info['test_class_distribution']}")
    if max_train or max_test:
        print(f"  subsampled for this run: train={len(y_train)} test={len(y_test)}")

    # Sanity: no leakage columns in the feature matrix.
    leaked = [c for c in x_train.columns if str(c).strip().lower() in {"label", "attack_cat"}]
    if leaked:
        raise RuntimeError(f"Target leakage columns present in features: {leaked}")

    preprocessor = build_preprocess_pipeline(
        splits.numeric_features,
        splits.categorical_features,
    )
    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", clf),
        ]
    )

    print(
        f"Training Random Forest (n_estimators={args.n_estimators}, "
        f"class_weight=balanced_subsample)...",
        flush=True,
    )
    start = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start
    print(f"  training finished in {train_seconds:.2f}s", flush=True)

    print("Evaluating on UNSW-NB15 test set...", flush=True)
    y_pred = model.predict(x_test)

    labels = sorted(set(y_test.astype(str)) | set(y_pred.astype(str)))
    report = classification_report(
        y_test,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    security = _binary_security_metrics(y_test, y_pred, UNSW_BENIGN_LABEL)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "macro_precision": round(
            float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4
        ),
        "macro_recall": round(
            float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4
        ),
        "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "attack_recall": security["attack_recall"],
        "false_positive_rate": security["false_positive_rate"],
        "false_negative_rate": security["false_negative_rate"],
        "detection_rate": security["detection_rate"],
        "training_seconds": round(float(train_seconds), 3),
    }

    payload = {
        "experiment": "UNSW-NB15 standalone evaluation",
        "dataset": "UNSW-NB15",
        "model": "Random Forest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "feature_count": int(x_train.shape[1]),
        "numeric_feature_count": info["numeric_feature_count"],
        "categorical_feature_count": info["categorical_feature_count"],
        "n_estimators": args.n_estimators,
        "class_weight": "balanced_subsample",
        "random_state": 42,
        "official_split_preserved": not bool(max_train or max_test),
        "quick_run": bool(args.quick or max_train or max_test),
        "train_class_distribution": class_distribution(y_train)
        if (max_train or max_test)
        else info["train_class_distribution"],
        "test_class_distribution": class_distribution(y_test)
        if (max_train or max_test)
        else info["test_class_distribution"],
        "metrics": metrics,
        "binary_confusion": {
            "tp": security["tp"],
            "tn": security["tn"],
            "fp": security["fp"],
            "fn": security["fn"],
            "benign_label": UNSW_BENIGN_LABEL,
        },
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": labels,
        "notes": [
            "UNSW-NB15 standalone evaluation does not constitute cross-dataset generalization.",
            "Cross-dataset evaluation will be performed separately after feature and label alignment.",
            "This artifact does not replace ml/saved_models/random_forest_model.pkl (CICIDS2017 production).",
            "Target leakage prevented: label and attack_cat excluded from features; id dropped.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Wrote {OUT_JSON}", flush=True)

    if not args.no_save_model:
        joblib.dump(model, OUT_MODEL)
        print(f"Wrote UNSW-only model {OUT_MODEL} (not production)", flush=True)

    print("\n=== UNSW-NB15 Standalone Evaluation ===")
    print(f"accuracy:       {metrics['accuracy']:.4f}")
    print(f"macro_precision:{metrics['macro_precision']:.4f}")
    print(f"macro_recall:   {metrics['macro_recall']:.4f}")
    print(f"macro_f1:       {metrics['macro_f1']:.4f}")
    print(f"attack_recall:  {metrics['attack_recall']:.4f}")
    print(f"FPR:            {metrics['false_positive_rate']:.4f}")
    print(f"FNR:            {metrics['false_negative_rate']:.4f}")


if __name__ == "__main__":
    main()
