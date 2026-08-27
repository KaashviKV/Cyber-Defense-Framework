"""
UNSW-NB15 Phase 1 analysis (standalone research artifact).

Adds deeper multiclass diagnostics, a dedicated binary Normal-vs-Attack RF,
ROC-AUC / PR-AUC, and feature importance — without touching production
CICIDS2017 models or the /analyze contract.

Usage:
  python scripts/analyze_unsw_nb15_phase1.py
  python scripts/analyze_unsw_nb15_phase1.py --quick
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
    average_precision_score,
    classification_report,
    confusion_matrix,
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

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_phase1_analysis.json"
MULTICLASS_MODEL = PROJECT_ROOT / "ml" / "saved_models" / "random_forest_unsw_nb15.pkl"
BINARY_MODEL = PROJECT_ROOT / "ml" / "saved_models" / "random_forest_unsw_nb15_binary.pkl"


def _to_binary_labels(y, benign: str = UNSW_BENIGN_LABEL) -> np.ndarray:
    """1 = attack, 0 = Normal."""
    return (np.asarray(y).astype(str) != benign).astype(int)


def _attack_score_from_multiclass(model: Pipeline, x, classes) -> np.ndarray:
    """P(attack) = 1 - P(Normal) from multiclass predict_proba."""
    proba = model.predict_proba(x)
    classes = [str(c) for c in classes]
    if UNSW_BENIGN_LABEL in classes:
        idx = classes.index(UNSW_BENIGN_LABEL)
        return 1.0 - proba[:, idx]
    return np.ones(len(x), dtype=float)


def _binary_auc_metrics(y_true_bin: np.ndarray, scores: np.ndarray) -> dict:
    if len(np.unique(y_true_bin)) < 2:
        return {"roc_auc": None, "pr_auc": None, "note": "Need both classes for AUC."}
    return {
        "roc_auc": round(float(roc_auc_score(y_true_bin, scores)), 4),
        "pr_auc": round(float(average_precision_score(y_true_bin, scores)), 4),
    }


def _per_class_table(y_true, y_pred, labels: list[str]) -> list[dict]:
    report = classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )
    rows = []
    for label in labels:
        row = report.get(label, {})
        rows.append(
            {
                "class": label,
                "precision": round(float(row.get("precision", 0.0)), 4),
                "recall": round(float(row.get("recall", 0.0)), 4),
                "f1": round(float(row.get("f1-score", 0.0)), 4),
                "support": int(row.get("support", 0)),
            }
        )
    return rows


def _confusion_analysis(y_true, y_pred, labels: list[str]) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    with np.errstate(divide="ignore", invalid="ignore"):
        row_sums = cm.sum(axis=1, keepdims=True)
        col_sums = cm.sum(axis=0, keepdims=True)
        row_norm = np.divide(cm, row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)
        col_norm = np.divide(cm, col_sums, out=np.zeros_like(cm, dtype=float), where=col_sums != 0)

    confusions = []
    for i, true_label in enumerate(labels):
        for j, pred_label in enumerate(labels):
            if i == j:
                continue
            count = int(cm[i, j])
            if count <= 0:
                continue
            confusions.append(
                {
                    "true": true_label,
                    "predicted": pred_label,
                    "count": count,
                    "share_of_true_class": round(float(row_norm[i, j]), 4),
                }
            )
    confusions.sort(key=lambda r: r["count"], reverse=True)

    return {
        "labels": labels,
        "matrix": cm.tolist(),
        "row_normalized": np.round(row_norm, 4).tolist(),
        "column_normalized": np.round(col_norm, 4).tolist(),
        "top_confusions": confusions[:25],
        "diagonal_correct": int(np.trace(cm)),
        "total": int(cm.sum()),
    }


def _original_feature_name(transformed_name: str) -> str:
    """Map ColumnTransformer output names back to original columns."""
    # Examples: num__sttl, cat__proto_tcp
    if transformed_name.startswith("num__"):
        return transformed_name[len("num__") :]
    if transformed_name.startswith("cat__"):
        rest = transformed_name[len("cat__") :]
        # OneHotEncoder names look like proto_tcp / service_http
        for prefix in ("proto_", "service_", "state_"):
            if rest.startswith(prefix):
                return prefix[:-1]
        if "_" in rest:
            return rest.rsplit("_", 1)[0]
        return rest
    return transformed_name


def _feature_importance(model: Pipeline, top_k: int = 30) -> dict:
    preprocess = model.named_steps["preprocess"]
    clf = model.named_steps["clf"]
    names = [str(n) for n in preprocess.get_feature_names_out()]
    importances = np.asarray(clf.feature_importances_, dtype=float)
    if len(names) != len(importances):
        raise RuntimeError("Feature name / importance length mismatch.")

    encoded = [
        {"feature": name, "importance": round(float(imp), 6)}
        for name, imp in sorted(zip(names, importances), key=lambda t: t[1], reverse=True)
    ]

    aggregated: dict[str, float] = {}
    for name, imp in zip(names, importances):
        key = _original_feature_name(name)
        aggregated[key] = aggregated.get(key, 0.0) + float(imp)
    original = [
        {"feature": feat, "importance": round(float(imp), 6)}
        for feat, imp in sorted(aggregated.items(), key=lambda t: t[1], reverse=True)
    ]

    return {
        "encoded_top": encoded[:top_k],
        "original_feature_top": original[:top_k],
        "encoded_feature_count": len(encoded),
        "original_feature_count": len(original),
    }


def _build_rf_pipeline(numeric, categorical, n_estimators: int, class_weight) -> Pipeline:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="UNSW-NB15 Phase 1 analysis")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument(
        "--retrain-multiclass",
        action="store_true",
        help="Ignore saved multiclass UNSW model and retrain.",
    )
    parser.add_argument("--no-save-binary-model", action="store_true")
    args = parser.parse_args()

    max_train = args.max_train if args.max_train is not None else (8000 if args.quick else None)
    max_test = args.max_test if args.max_test is not None else (3000 if args.quick else None)

    print("Loading UNSW-NB15 splits for Phase 1 analysis...", flush=True)
    splits = load_unsw_nb15_splits(PROJECT_ROOT)
    info = describe_splits(splits)
    x_train, y_train = _maybe_subsample(splits.x_train, splits.y_train, max_train, seed=42)
    x_test, y_test = _maybe_subsample(splits.x_test, splits.y_test, max_test, seed=0)

    leaked = [c for c in x_train.columns if str(c).strip().lower() in {"label", "attack_cat"}]
    if leaked:
        raise RuntimeError(f"Target leakage columns present: {leaked}")

    print(f"  train={x_train.shape} test={x_test.shape} features={x_train.shape[1]}", flush=True)

    # --- Multiclass model (reuse saved artifact when possible) ---
    if MULTICLASS_MODEL.exists() and not args.retrain_multiclass and not (max_train or max_test):
        print(f"Loading multiclass model from {MULTICLASS_MODEL}", flush=True)
        multi_model = joblib.load(MULTICLASS_MODEL)
        multi_train_seconds = None
    else:
        print("Training multiclass Random Forest...", flush=True)
        multi_model = _build_rf_pipeline(
            splits.numeric_features,
            splits.categorical_features,
            args.n_estimators,
            class_weight="balanced_subsample",
        )
        t0 = time.perf_counter()
        multi_model.fit(x_train, y_train)
        multi_train_seconds = round(time.perf_counter() - t0, 3)
        print(f"  multiclass train time: {multi_train_seconds}s", flush=True)

    y_pred_multi = multi_model.predict(x_test)
    labels = sorted(set(y_test.astype(str)) | set(np.asarray(y_pred_multi).astype(str)))
    multi_security = _binary_security_metrics(y_test, y_pred_multi)
    y_test_bin = _to_binary_labels(y_test)
    multi_scores = _attack_score_from_multiclass(multi_model, x_test, multi_model.classes_)
    multi_auc = _binary_auc_metrics(y_test_bin, multi_scores)

    multiclass_block = {
        "task": "multiclass_attack_cat",
        "metrics": {
            "accuracy": round(float(accuracy_score(y_test, y_pred_multi)), 4),
            "macro_precision": round(
                float(precision_score(y_test, y_pred_multi, average="macro", zero_division=0)), 4
            ),
            "macro_recall": round(
                float(recall_score(y_test, y_pred_multi, average="macro", zero_division=0)), 4
            ),
            "macro_f1": round(
                float(f1_score(y_test, y_pred_multi, average="macro", zero_division=0)), 4
            ),
            "attack_recall": multi_security["attack_recall"],
            "false_positive_rate": multi_security["false_positive_rate"],
            "false_negative_rate": multi_security["false_negative_rate"],
            "roc_auc_normal_vs_attack": multi_auc["roc_auc"],
            "pr_auc_normal_vs_attack": multi_auc["pr_auc"],
            "training_seconds": multi_train_seconds,
        },
        "per_class": _per_class_table(y_test, y_pred_multi, labels),
        "confusion_matrix_analysis": _confusion_analysis(y_test, y_pred_multi, labels),
        "binary_collapse": {
            "tp": multi_security["tp"],
            "tn": multi_security["tn"],
            "fp": multi_security["fp"],
            "fn": multi_security["fn"],
            "note": "Multiclass predictions collapsed: any non-Normal class counts as attack.",
        },
        "feature_importance": _feature_importance(multi_model),
    }

    # --- Dedicated binary Normal-vs-Attack experiment ---
    print("Training dedicated binary Normal-vs-Attack Random Forest...", flush=True)
    y_train_bin = _to_binary_labels(y_train)
    binary_model = _build_rf_pipeline(
        splits.numeric_features,
        splits.categorical_features,
        args.n_estimators,
        class_weight="balanced_subsample",
    )
    t0 = time.perf_counter()
    binary_model.fit(x_train, y_train_bin)
    binary_train_seconds = round(time.perf_counter() - t0, 3)
    y_pred_bin = binary_model.predict(x_test)
    # Attack probability = P(class=1)
    classes_bin = [int(c) for c in binary_model.classes_]
    proba_bin = binary_model.predict_proba(x_test)
    attack_idx = classes_bin.index(1) if 1 in classes_bin else -1
    scores_bin = proba_bin[:, attack_idx] if attack_idx >= 0 else proba_bin[:, -1]
    bin_auc = _binary_auc_metrics(y_test_bin, scores_bin)

    # Map binary preds back to Normal/Attack strings for shared security helper.
    y_pred_bin_str = np.where(y_pred_bin == 0, UNSW_BENIGN_LABEL, "Attack")
    y_test_bin_str = np.where(y_test_bin == 0, UNSW_BENIGN_LABEL, "Attack")
    bin_security = _binary_security_metrics(y_test_bin_str, y_pred_bin_str, UNSW_BENIGN_LABEL)
    bin_cm = confusion_matrix(y_test_bin, y_pred_bin, labels=[0, 1])

    binary_block = {
        "task": "binary_normal_vs_attack",
        "positive_class": "Attack",
        "negative_class": UNSW_BENIGN_LABEL,
        "metrics": {
            "accuracy": round(float(accuracy_score(y_test_bin, y_pred_bin)), 4),
            "precision_attack": round(
                float(precision_score(y_test_bin, y_pred_bin, zero_division=0)), 4
            ),
            "recall_attack": round(
                float(recall_score(y_test_bin, y_pred_bin, zero_division=0)), 4
            ),
            "f1_attack": round(float(f1_score(y_test_bin, y_pred_bin, zero_division=0)), 4),
            "attack_recall": bin_security["attack_recall"],
            "false_positive_rate": bin_security["false_positive_rate"],
            "false_negative_rate": bin_security["false_negative_rate"],
            "roc_auc": bin_auc["roc_auc"],
            "pr_auc": bin_auc["pr_auc"],
            "training_seconds": binary_train_seconds,
        },
        "confusion_matrix": {
            "labels": ["Normal(0)", "Attack(1)"],
            "matrix": bin_cm.tolist(),
            "tp": bin_security["tp"],
            "tn": bin_security["tn"],
            "fp": bin_security["fp"],
            "fn": bin_security["fn"],
        },
        "feature_importance": _feature_importance(binary_model),
    }

    if not args.no_save_binary_model and not (max_train or max_test):
        joblib.dump(binary_model, BINARY_MODEL)
        print(f"Wrote binary UNSW model {BINARY_MODEL} (not production)", flush=True)

    payload = {
        "experiment": "UNSW-NB15 Phase 1 analysis",
        "dataset": "UNSW-NB15",
        "phase": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "feature_count": int(x_train.shape[1]),
        "numeric_feature_count": info["numeric_feature_count"],
        "categorical_feature_count": info["categorical_feature_count"],
        "official_split_preserved": not bool(max_train or max_test),
        "quick_run": bool(args.quick or max_train or max_test),
        "train_class_distribution": class_distribution(y_train),
        "test_class_distribution": class_distribution(y_test),
        "research_focus": {
            "observation": (
                "Multiclass RF can achieve high attack recall while still producing a high "
                "false-positive rate on Normal traffic — costly for SOC analysts."
            ),
            "question": (
                "Can we maintain high attack detection while reducing false positives "
                "(via CTI enrichment, risk fusion, and DQN prioritization)?"
            ),
        },
        "multiclass": multiclass_block,
        "binary_normal_vs_attack": binary_block,
        "summary": {
            "multiclass_macro_f1": multiclass_block["metrics"]["macro_f1"],
            "multiclass_attack_recall": multiclass_block["metrics"]["attack_recall"],
            "multiclass_fpr": multiclass_block["metrics"]["false_positive_rate"],
            "multiclass_roc_auc": multiclass_block["metrics"]["roc_auc_normal_vs_attack"],
            "multiclass_pr_auc": multiclass_block["metrics"]["pr_auc_normal_vs_attack"],
            "binary_attack_recall": binary_block["metrics"]["attack_recall"],
            "binary_fpr": binary_block["metrics"]["false_positive_rate"],
            "binary_roc_auc": binary_block["metrics"]["roc_auc"],
            "binary_pr_auc": binary_block["metrics"]["pr_auc"],
            "top_original_features_multiclass": [
                row["feature"]
                for row in multiclass_block["feature_importance"]["original_feature_top"][:10]
            ],
        },
        "notes": [
            "Phase 1 only: confusion analysis, per-class metrics, binary experiment, AUC, importance.",
            "Does not constitute cross-dataset generalization.",
            "Does not replace production CICIDS2017 random_forest_model.pkl.",
            "Binary experiment trains a separate RF on Normal vs Attack labels derived from attack_cat.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Wrote {OUT_JSON}", flush=True)

    s = payload["summary"]
    print("\n=== UNSW-NB15 Phase 1 Summary ===")
    print(
        f"multiclass: macro-F1={s['multiclass_macro_f1']} "
        f"attack_recall={s['multiclass_attack_recall']} "
        f"FPR={s['multiclass_fpr']} "
        f"ROC-AUC={s['multiclass_roc_auc']} PR-AUC={s['multiclass_pr_auc']}"
    )
    print(
        f"binary:     attack_recall={s['binary_attack_recall']} "
        f"FPR={s['binary_fpr']} "
        f"ROC-AUC={s['binary_roc_auc']} PR-AUC={s['binary_pr_auc']}"
    )
    print(f"top features: {', '.join(s['top_original_features_multiclass'])}")


if __name__ == "__main__":
    main()
