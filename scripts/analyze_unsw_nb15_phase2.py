"""
UNSW-NB15 Phase 2 — class-imbalance comparison.

Compares Random Forest strategies on the official UNSW train/test split:
  1) unweighted (class_weight=None)
  2) balanced (class_weight="balanced_subsample")
  3) random oversampling of minority classes on TRAIN only

Does not touch production CICIDS2017 models or /analyze.

Usage:
  python scripts/analyze_unsw_nb15_phase2.py
  python scripts/analyze_unsw_nb15_phase2.py --quick
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
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
from scripts.evaluate_unsw_nb15 import (  # noqa: E402
    _binary_security_metrics,
    _maybe_subsample,
)

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_phase2_imbalance.json"


def _to_binary_labels(y, benign: str = UNSW_BENIGN_LABEL) -> np.ndarray:
    return (np.asarray(y).astype(str) != benign).astype(int)


def _attack_score_from_multiclass(model: Pipeline, x) -> np.ndarray:
    proba = model.predict_proba(x)
    classes = [str(c) for c in model.classes_]
    if UNSW_BENIGN_LABEL in classes:
        return 1.0 - proba[:, classes.index(UNSW_BENIGN_LABEL)]
    return np.ones(len(x), dtype=float)


def _auc_pair(y_true_bin: np.ndarray, scores: np.ndarray) -> dict:
    if len(np.unique(y_true_bin)) < 2:
        return {"roc_auc": None, "pr_auc": None}
    return {
        "roc_auc": round(float(roc_auc_score(y_true_bin, scores)), 4),
        "pr_auc": round(float(average_precision_score(y_true_bin, scores)), 4),
    }


def random_oversample(
    x: pd.DataFrame,
    y: pd.Series,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """
    Random oversample minority classes on TRAIN only up to the majority count.

    No synthetic feature generation (does not require imbalanced-learn).
    Test set is never oversampled.
    """
    rng = np.random.default_rng(random_state)
    y_arr = np.asarray(y).astype(str)
    classes, counts = np.unique(y_arr, return_counts=True)
    target = int(counts.max())
    parts: list[np.ndarray] = []
    before = {str(c): int(n) for c, n in zip(classes, counts)}
    after: dict[str, int] = {}
    for cls, count in zip(classes, counts):
        idx = np.flatnonzero(y_arr == cls)
        if count < target:
            extra = rng.choice(idx, size=target - count, replace=True)
            taken = np.concatenate([idx, extra])
        else:
            taken = idx
        parts.append(taken)
        after[str(cls)] = int(len(taken))
    all_idx = np.concatenate(parts)
    rng.shuffle(all_idx)
    x_out = x.iloc[all_idx].reset_index(drop=True)
    y_out = pd.Series(y_arr[all_idx], name=getattr(y, "name", None))
    return x_out, y_out, {"before": before, "after": after, "target_per_class": target}


def _build_pipeline(numeric, categorical, n_estimators: int, class_weight) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocess_pipeline(numeric, categorical)),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    random_state=42,
                    n_jobs=-1,
                    class_weight=class_weight,
                ),
            ),
        ]
    )


def _eval_multiclass(model: Pipeline, x_test, y_test) -> dict:
    y_pred = model.predict(x_test)
    security = _binary_security_metrics(y_test, y_pred)
    y_bin = _to_binary_labels(y_test)
    scores = _attack_score_from_multiclass(model, x_test)
    auc = _auc_pair(y_bin, scores)
    return {
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
        "roc_auc": auc["roc_auc"],
        "pr_auc": auc["pr_auc"],
        "tp": security["tp"],
        "tn": security["tn"],
        "fp": security["fp"],
        "fn": security["fn"],
    }


def _eval_binary(model: Pipeline, x_test, y_test_bin: np.ndarray) -> dict:
    y_pred = model.predict(x_test)
    classes = [int(c) for c in model.classes_]
    proba = model.predict_proba(x_test)
    attack_idx = classes.index(1) if 1 in classes else len(classes) - 1
    scores = proba[:, attack_idx]
    y_pred_str = np.where(y_pred == 0, UNSW_BENIGN_LABEL, "Attack")
    y_true_str = np.where(y_test_bin == 0, UNSW_BENIGN_LABEL, "Attack")
    security = _binary_security_metrics(y_true_str, y_pred_str)
    auc = _auc_pair(y_test_bin, scores)
    return {
        "accuracy": round(float(accuracy_score(y_test_bin, y_pred)), 4),
        "precision_attack": round(
            float(precision_score(y_test_bin, y_pred, zero_division=0)), 4
        ),
        "recall_attack": round(float(recall_score(y_test_bin, y_pred, zero_division=0)), 4),
        "f1_attack": round(float(f1_score(y_test_bin, y_pred, zero_division=0)), 4),
        "attack_recall": security["attack_recall"],
        "false_positive_rate": security["false_positive_rate"],
        "false_negative_rate": security["false_negative_rate"],
        "roc_auc": auc["roc_auc"],
        "pr_auc": auc["pr_auc"],
        "tp": security["tp"],
        "tn": security["tn"],
        "fp": security["fp"],
        "fn": security["fn"],
    }


def _run_strategy(
    name: str,
    description: str,
    x_train,
    y_train,
    x_test,
    y_test,
    numeric,
    categorical,
    n_estimators: int,
    class_weight,
    oversample: bool,
) -> dict:
    print(f"\n=== Strategy: {name} ===", flush=True)
    oversample_info = None
    x_fit, y_fit = x_train, y_train
    if oversample:
        x_fit, y_fit, oversample_info = random_oversample(x_train, y_train, random_state=42)
        print(
            f"  oversampled train rows: {len(y_train)} -> {len(y_fit)} "
            f"(target_per_class={oversample_info['target_per_class']})",
            flush=True,
        )

    model = _build_pipeline(numeric, categorical, n_estimators, class_weight)
    t0 = time.perf_counter()
    model.fit(x_fit, y_fit)
    train_seconds = round(time.perf_counter() - t0, 3)
    print(f"  multiclass trained in {train_seconds}s", flush=True)
    multi_metrics = _eval_multiclass(model, x_test, y_test)
    multi_metrics["training_seconds"] = train_seconds
    multi_metrics["train_rows_used"] = int(len(y_fit))

    # Dedicated binary Normal-vs-Attack with the same imbalance strategy.
    y_train_bin = pd.Series(_to_binary_labels(y_train), name="binary")
    y_test_bin = _to_binary_labels(y_test)
    x_bin_fit, y_bin_fit = x_train, y_train_bin
    binary_oversample_info = None
    if oversample:
        x_bin_fit, y_bin_fit, binary_oversample_info = random_oversample(
            x_train, y_train_bin.astype(str), random_state=42
        )
        # Map back to 0/1 ints after oversampling string labels "0"/"1"
        y_bin_fit = y_bin_fit.astype(int)

    bin_model = _build_pipeline(numeric, categorical, n_estimators, class_weight)
    t0 = time.perf_counter()
    bin_model.fit(x_bin_fit, y_bin_fit)
    bin_seconds = round(time.perf_counter() - t0, 3)
    print(f"  binary trained in {bin_seconds}s", flush=True)
    bin_metrics = _eval_binary(bin_model, x_test, y_test_bin)
    bin_metrics["training_seconds"] = bin_seconds
    bin_metrics["train_rows_used"] = int(len(y_bin_fit))

    print(
        f"  multiclass: macro-F1={multi_metrics['macro_f1']} "
        f"attack_recall={multi_metrics['attack_recall']} "
        f"FPR={multi_metrics['false_positive_rate']}",
        flush=True,
    )
    print(
        f"  binary:     attack_recall={bin_metrics['attack_recall']} "
        f"FPR={bin_metrics['false_positive_rate']} "
        f"ROC-AUC={bin_metrics['roc_auc']}",
        flush=True,
    )

    return {
        "name": name,
        "description": description,
        "class_weight": class_weight,
        "oversample_train": oversample,
        "multiclass_oversample": oversample_info,
        "binary_oversample": binary_oversample_info,
        "multiclass": multi_metrics,
        "binary_normal_vs_attack": bin_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="UNSW-NB15 Phase 2 imbalance comparison")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    max_train = args.max_train if args.max_train is not None else (8000 if args.quick else None)
    max_test = args.max_test if args.max_test is not None else (3000 if args.quick else None)

    print("Loading UNSW-NB15 splits for Phase 2...", flush=True)
    splits = load_unsw_nb15_splits(PROJECT_ROOT)
    info = describe_splits(splits)
    x_train, y_train = _maybe_subsample(splits.x_train, splits.y_train, max_train, seed=42)
    x_test, y_test = _maybe_subsample(splits.x_test, splits.y_test, max_test, seed=0)

    leaked = [c for c in x_train.columns if str(c).strip().lower() in {"label", "attack_cat"}]
    if leaked:
        raise RuntimeError(f"Target leakage columns present: {leaked}")

    print(f"  train={x_train.shape} test={x_test.shape}", flush=True)
    print(f"  train class distribution: {class_distribution(y_train)}", flush=True)

    strategies = [
        (
            "rf_unweighted",
            "Random Forest with class_weight=None (no imbalance handling).",
            None,
            False,
        ),
        (
            "rf_balanced",
            "Random Forest with class_weight='balanced_subsample'.",
            "balanced_subsample",
            False,
        ),
        (
            "rf_oversampled",
            "Random oversample minority classes on TRAIN only, then RF with class_weight=None.",
            None,
            True,
        ),
    ]

    results = []
    for name, desc, weight, do_os in strategies:
        results.append(
            _run_strategy(
                name=name,
                description=desc,
                x_train=x_train,
                y_train=y_train,
                x_test=x_test,
                y_test=y_test,
                numeric=splits.numeric_features,
                categorical=splits.categorical_features,
                n_estimators=args.n_estimators,
                class_weight=weight,
                oversample=do_os,
            )
        )

    # Pick best by lowest FPR among strategies with attack_recall >= 0.95 (binary), else best F1.
    binary_rows = [
        {
            "name": r["name"],
            "attack_recall": r["binary_normal_vs_attack"]["attack_recall"],
            "false_positive_rate": r["binary_normal_vs_attack"]["false_positive_rate"],
            "macro_f1_multiclass": r["multiclass"]["macro_f1"],
            "roc_auc": r["binary_normal_vs_attack"]["roc_auc"],
        }
        for r in results
    ]
    high_recall = [row for row in binary_rows if (row["attack_recall"] or 0) >= 0.95]
    if high_recall:
        best = min(high_recall, key=lambda r: r["false_positive_rate"])
        best_rule = "lowest binary FPR among strategies with attack_recall >= 0.95"
    else:
        best = max(binary_rows, key=lambda r: r["attack_recall"] or 0)
        best_rule = "highest binary attack_recall (no strategy reached 0.95 recall)"

    payload = {
        "experiment": "UNSW-NB15 Phase 2 class imbalance comparison",
        "dataset": "UNSW-NB15",
        "phase": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "feature_count": int(x_train.shape[1]),
        "n_estimators": args.n_estimators,
        "official_split_preserved": not bool(max_train or max_test),
        "quick_run": bool(args.quick or max_train or max_test),
        "train_class_distribution": class_distribution(y_train),
        "test_class_distribution": class_distribution(y_test),
        "numeric_feature_count": info["numeric_feature_count"],
        "categorical_feature_count": info["categorical_feature_count"],
        "strategies": results,
        "comparison_table": [
            {
                "strategy": r["name"],
                "multiclass_macro_f1": r["multiclass"]["macro_f1"],
                "multiclass_attack_recall": r["multiclass"]["attack_recall"],
                "multiclass_fpr": r["multiclass"]["false_positive_rate"],
                "binary_attack_recall": r["binary_normal_vs_attack"]["attack_recall"],
                "binary_fpr": r["binary_normal_vs_attack"]["false_positive_rate"],
                "binary_roc_auc": r["binary_normal_vs_attack"]["roc_auc"],
                "binary_pr_auc": r["binary_normal_vs_attack"]["pr_auc"],
            }
            for r in results
        ],
        "best_for_soc_fpr": {
            "strategy": best["name"],
            "rule": best_rule,
            "binary_attack_recall": best["attack_recall"],
            "binary_false_positive_rate": best["false_positive_rate"],
        },
        "research_focus": {
            "question": (
                "Does class weighting or train-only oversampling reduce false positives "
                "while preserving high attack recall?"
            ),
            "note": (
                "Even if attack recall stays high, a large FPR remains a SOC cost; "
                "CTI + risk fusion + DQN still matter for prioritization."
            ),
        },
        "notes": [
            "Oversampling uses random replacement of minority-class rows (no SMOTE dependency).",
            "Oversampling is applied to the training set only; the official test split is unchanged.",
            "Does not replace production CICIDS2017 random_forest_model.pkl.",
            "Not cross-dataset generalization.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\nWrote {OUT_JSON}", flush=True)
    print("\n=== Phase 2 comparison ===")
    print(
        f"{'strategy':<18} {'mF1':>7} {'mAR':>7} {'mFPR':>7} {'bAR':>7} {'bFPR':>7} {'bAUC':>7}"
    )
    for row in payload["comparison_table"]:
        print(
            f"{row['strategy']:<18} "
            f"{row['multiclass_macro_f1']:>7.4f} "
            f"{row['multiclass_attack_recall']:>7.4f} "
            f"{row['multiclass_fpr']:>7.4f} "
            f"{row['binary_attack_recall']:>7.4f} "
            f"{row['binary_fpr']:>7.4f} "
            f"{(row['binary_roc_auc'] or 0):>7.4f}"
        )
    print(
        f"Best for SOC FPR focus: {best['name']} "
        f"(binary AR={best['attack_recall']}, FPR={best['false_positive_rate']})"
    )


if __name__ == "__main__":
    main()
