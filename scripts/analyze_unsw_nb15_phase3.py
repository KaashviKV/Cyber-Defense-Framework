"""
UNSW-NB15 Phase 3 — feature ablation (42 / 30 / 20 / 10).

Ranks original features by multiclass RF importance, then retrains on the
top-k subsets. Reports attack recall and FPR so the detection–noise trade-off
is visible.

Does not touch production CICIDS2017 models or /analyze.

Usage:
  python scripts/analyze_unsw_nb15_phase3.py
  python scripts/analyze_unsw_nb15_phase3.py --quick
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
from scripts.analyze_unsw_nb15_phase1 import (  # noqa: E402
    _feature_importance,
    _to_binary_labels,
)
from scripts.evaluate_unsw_nb15 import (  # noqa: E402
    _binary_security_metrics,
    _maybe_subsample,
)

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_phase3_feature_ablation.json"
PHASE1_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_phase1_analysis.json"
FEATURE_COUNTS = (42, 30, 20, 10)


def _auc_pair(y_true_bin: np.ndarray, scores: np.ndarray) -> dict:
    if len(np.unique(y_true_bin)) < 2:
        return {"roc_auc": None, "pr_auc": None}
    return {
        "roc_auc": round(float(roc_auc_score(y_true_bin, scores)), 4),
        "pr_auc": round(float(average_precision_score(y_true_bin, scores)), 4),
    }


def _attack_score_from_multiclass(model: Pipeline, x) -> np.ndarray:
    proba = model.predict_proba(x)
    classes = [str(c) for c in model.classes_]
    if UNSW_BENIGN_LABEL in classes:
        return 1.0 - proba[:, classes.index(UNSW_BENIGN_LABEL)]
    return np.ones(len(x), dtype=float)


def _build_pipeline(numeric, categorical, n_estimators: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocess_pipeline(numeric, categorical)),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                ),
            ),
        ]
    )


def _split_types(cols: list[str], all_numeric: list[str], all_cat: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in cols if c in all_numeric]
    categorical = [c for c in cols if c in all_cat]
    return numeric, categorical


def _rank_features(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    numeric: list[str],
    categorical: list[str],
    n_estimators: int,
) -> list[str]:
    """Prefer Phase 1 importance ranking when available; else fit a full model."""
    if PHASE1_JSON.exists():
        try:
            with open(PHASE1_JSON, encoding="utf-8") as fh:
                phase1 = json.load(fh)
            ranked = [
                row["feature"]
                for row in phase1["multiclass"]["feature_importance"]["original_feature_top"]
            ]
            # Keep only features present in current matrix; append any missing at end.
            present = list(x_train.columns)
            ordered = [f for f in ranked if f in present]
            for f in present:
                if f not in ordered:
                    ordered.append(f)
            if len(ordered) == len(present):
                print("Using feature ranking from Phase 1 multiclass importance.", flush=True)
                return ordered
        except (KeyError, TypeError, json.JSONDecodeError):
            pass

    print("Fitting full model to rank features...", flush=True)
    model = _build_pipeline(numeric, categorical, n_estimators)
    model.fit(x_train, y_train)
    ranked = [row["feature"] for row in _feature_importance(model)["original_feature_top"]]
    present = list(x_train.columns)
    ordered = [f for f in ranked if f in present]
    for f in present:
        if f not in ordered:
            ordered.append(f)
    return ordered


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


def main() -> None:
    parser = argparse.ArgumentParser(description="UNSW-NB15 Phase 3 feature ablation")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    max_train = args.max_train if args.max_train is not None else (8000 if args.quick else None)
    max_test = args.max_test if args.max_test is not None else (3000 if args.quick else None)

    print("Loading UNSW-NB15 splits for Phase 3 feature ablation...", flush=True)
    splits = load_unsw_nb15_splits(PROJECT_ROOT)
    info = describe_splits(splits)
    x_train, y_train = _maybe_subsample(splits.x_train, splits.y_train, max_train, seed=42)
    x_test, y_test = _maybe_subsample(splits.x_test, splits.y_test, max_test, seed=0)
    y_test_bin = _to_binary_labels(y_test)
    y_train_bin = _to_binary_labels(y_train)

    full_count = int(x_train.shape[1])
    print(f"  train={x_train.shape} test={x_test.shape} full_features={full_count}", flush=True)

    ranked = _rank_features(
        x_train,
        y_train,
        splits.numeric_features,
        splits.categorical_features,
        args.n_estimators,
    )
    print(f"  ranked features ({len(ranked)}): {ranked[:10]} ...", flush=True)

    results = []
    for k in FEATURE_COUNTS:
        k_eff = min(k, full_count)
        selected = ranked[:k_eff]
        numeric, categorical = _split_types(
            selected, splits.numeric_features, splits.categorical_features
        )
        print(
            f"\n=== Top-{k_eff} features "
            f"(numeric={len(numeric)}, categorical={len(categorical)}) ===",
            flush=True,
        )
        print(f"  selected: {selected}", flush=True)

        xtr = x_train[selected]
        xte = x_test[selected]

        multi = _build_pipeline(numeric, categorical, args.n_estimators)
        t0 = time.perf_counter()
        multi.fit(xtr, y_train)
        multi_sec = round(time.perf_counter() - t0, 3)
        multi_metrics = _eval_multiclass(multi, xte, y_test)
        multi_metrics["training_seconds"] = multi_sec

        binary = _build_pipeline(numeric, categorical, args.n_estimators)
        t0 = time.perf_counter()
        binary.fit(xtr, y_train_bin)
        bin_sec = round(time.perf_counter() - t0, 3)
        bin_metrics = _eval_binary(binary, xte, y_test_bin)
        bin_metrics["training_seconds"] = bin_sec

        print(
            f"  multiclass: macro-F1={multi_metrics['macro_f1']} "
            f"AR={multi_metrics['attack_recall']} FPR={multi_metrics['false_positive_rate']} "
            f"({multi_sec}s)",
            flush=True,
        )
        print(
            f"  binary:     AR={bin_metrics['attack_recall']} "
            f"FPR={bin_metrics['false_positive_rate']} "
            f"ROC-AUC={bin_metrics['roc_auc']} ({bin_sec}s)",
            flush=True,
        )

        results.append(
            {
                "feature_count": k_eff,
                "requested_feature_count": k,
                "selected_features": selected,
                "numeric_features": numeric,
                "categorical_features": categorical,
                "multiclass": multi_metrics,
                "binary_normal_vs_attack": bin_metrics,
            }
        )

    comparison = [
        {
            "feature_count": row["feature_count"],
            "multiclass_macro_f1": row["multiclass"]["macro_f1"],
            "multiclass_attack_recall": row["multiclass"]["attack_recall"],
            "multiclass_fpr": row["multiclass"]["false_positive_rate"],
            "binary_attack_recall": row["binary_normal_vs_attack"]["attack_recall"],
            "binary_fpr": row["binary_normal_vs_attack"]["false_positive_rate"],
            "binary_roc_auc": row["binary_normal_vs_attack"]["roc_auc"],
            "binary_pr_auc": row["binary_normal_vs_attack"]["pr_auc"],
        }
        for row in results
    ]

    # Prefer configurations that keep high recall while lowering FPR vs full set.
    full_fpr = next(
        (r["binary_fpr"] for r in comparison if r["feature_count"] == full_count),
        comparison[0]["binary_fpr"],
    )
    candidates = [
        r
        for r in comparison
        if (r["binary_attack_recall"] or 0) >= 0.95
    ]
    if candidates:
        best = min(candidates, key=lambda r: (r["binary_fpr"], -r["feature_count"]))
        best_rule = "lowest binary FPR among subsets with attack_recall >= 0.95"
    else:
        best = max(comparison, key=lambda r: r["binary_attack_recall"] or 0)
        best_rule = "highest binary attack_recall"

    payload = {
        "experiment": "UNSW-NB15 Phase 3 feature ablation",
        "dataset": "UNSW-NB15",
        "phase": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "full_feature_count": full_count,
        "feature_counts_evaluated": [row["feature_count"] for row in results],
        "feature_ranking": ranked,
        "ranking_source": "phase1_multiclass_importance"
        if PHASE1_JSON.exists()
        else "fitted_full_model",
        "class_weight": "balanced_subsample",
        "n_estimators": args.n_estimators,
        "official_split_preserved": not bool(max_train or max_test),
        "quick_run": bool(args.quick or max_train or max_test),
        "train_class_distribution": class_distribution(y_train),
        "test_class_distribution": class_distribution(y_test),
        "numeric_feature_count_full": info["numeric_feature_count"],
        "categorical_feature_count_full": info["categorical_feature_count"],
        "results": results,
        "comparison_table": comparison,
        "best_subset": {
            "feature_count": best["feature_count"],
            "rule": best_rule,
            "binary_attack_recall": best["binary_attack_recall"],
            "binary_false_positive_rate": best["binary_fpr"],
            "full_model_binary_fpr": full_fpr,
        },
        "research_focus": {
            "question": (
                "Can a smaller feature subset preserve high attack recall while reducing "
                "false positives (or at least quantify the trade-off)?"
            ),
            "note": (
                "Feature reduction alone may not solve SOC alert fatigue; CTI + risk + DQN "
                "remain relevant for prioritization."
            ),
        },
        "notes": [
            "Features ranked by original-column importance aggregated from one-hot encodings.",
            "Each subset retrains RF from scratch on the official UNSW train split.",
            "Does not replace production CICIDS2017 random_forest_model.pkl.",
            "Not cross-dataset generalization.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\nWrote {OUT_JSON}", flush=True)

    print("\n=== Phase 3 feature ablation ===")
    print(f"{'k':>4} {'mF1':>7} {'mAR':>7} {'mFPR':>7} {'bAR':>7} {'bFPR':>7} {'bAUC':>7}")
    for row in comparison:
        print(
            f"{row['feature_count']:>4} "
            f"{row['multiclass_macro_f1']:>7.4f} "
            f"{row['multiclass_attack_recall']:>7.4f} "
            f"{row['multiclass_fpr']:>7.4f} "
            f"{row['binary_attack_recall']:>7.4f} "
            f"{row['binary_fpr']:>7.4f} "
            f"{(row['binary_roc_auc'] or 0):>7.4f}"
        )
    print(
        f"Best subset under SOC rule: k={best['feature_count']} "
        f"(binary AR={best['binary_attack_recall']}, FPR={best['binary_fpr']})"
    )


if __name__ == "__main__":
    main()
