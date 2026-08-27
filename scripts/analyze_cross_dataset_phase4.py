"""
UNSW-NB15 Phase 4 — cross-dataset evaluation (binary Normal/BENIGN vs Attack).

Directions:
  1) CICIDS2017 train -> UNSW-NB15 test
  2) UNSW-NB15 train -> CICIDS2017 test

Uses a documented numeric feature alignment (see
ml/datasets/cross_dataset_alignment.py). This does NOT modify production
models or the 78-feature /analyze contract.

Usage:
  python scripts/analyze_cross_dataset_phase4.py
  python scripts/analyze_cross_dataset_phase4.py --quick
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
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.cross_dataset_alignment import (  # noqa: E402
    ALIGNED_FEATURES,
    alignment_documentation,
    cicids_labels_to_binary,
    cicids_matrix_to_aligned,
    shared_feature_names,
    unsw_frame_to_aligned,
    unsw_labels_to_binary,
)
from ml.datasets.unsw_nb15 import load_unsw_nb15_splits  # noqa: E402
from scripts.evaluate_unsw_nb15 import _maybe_subsample  # noqa: E402

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "cross_dataset_phase4.json"
CICIDS_PKL = PROJECT_ROOT / "dataset" / "CICIDS2017" / "processed" / "train_test_data.pkl"


def _binary_security(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    yt = np.asarray(y_true).astype(int)
    yp = np.asarray(y_pred).astype(int)
    tp = int(np.sum((yt == 1) & (yp == 1)))
    tn = int(np.sum((yt == 0) & (yp == 0)))
    fp = int(np.sum((yt == 0) & (yp == 1)))
    fn = int(np.sum((yt == 1) & (yp == 0)))
    attack_recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    return {
        "attack_recall": round(float(attack_recall), 4),
        "false_positive_rate": round(float(fpr), 4),
        "false_negative_rate": round(float(fnr), 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def _metrics(y_true, y_pred, scores) -> dict:
    security = _binary_security(y_true, y_pred)
    roc = pr = None
    if len(np.unique(y_true)) > 1:
        roc = round(float(roc_auc_score(y_true, scores)), 4)
        pr = round(float(average_precision_score(y_true, scores)), 4)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_attack": round(
            float(precision_score(y_true, y_pred, zero_division=0)), 4
        ),
        "recall_attack": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_attack": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "attack_recall": security["attack_recall"],
        "false_positive_rate": security["false_positive_rate"],
        "false_negative_rate": security["false_negative_rate"],
        "roc_auc": roc,
        "pr_auc": pr,
        "tp": security["tp"],
        "tn": security["tn"],
        "fp": security["fp"],
        "fn": security["fn"],
    }


def _build_model(n_estimators: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
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


def _subsample_xy(x: np.ndarray, y: np.ndarray, max_rows: int | None, seed: int):
    if not max_rows or len(y) <= max_rows:
        return x, y
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(y), size=max_rows, replace=False)
    return x[idx], y[idx]


def _run_transfer(
    name: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    n_estimators: int,
) -> dict:
    print(f"\n=== {name} ===", flush=True)
    print(f"  train={x_train.shape} test={x_test.shape}", flush=True)
    model = _build_model(n_estimators)
    t0 = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = round(time.perf_counter() - t0, 3)
    y_pred = model.predict(x_test)
    proba = model.predict_proba(x_test)
    classes = [int(c) for c in model.classes_]
    attack_idx = classes.index(1) if 1 in classes else len(classes) - 1
    scores = proba[:, attack_idx]
    metrics = _metrics(y_test, y_pred, scores)
    metrics["training_seconds"] = train_seconds
    print(
        f"  AR={metrics['attack_recall']} FPR={metrics['false_positive_rate']} "
        f"ROC-AUC={metrics['roc_auc']} F1={metrics['f1_attack']} ({train_seconds}s)",
        flush=True,
    )
    return {
        "name": name,
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "feature_count": int(x_train.shape[1]),
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 cross-dataset evaluation")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    max_train = args.max_train if args.max_train is not None else (12000 if args.quick else None)
    max_test = args.max_test if args.max_test is not None else (4000 if args.quick else None)

    if not CICIDS_PKL.exists():
        raise FileNotFoundError(
            f"CICIDS processed split missing at {CICIDS_PKL}. "
            "Phase 4 needs dataset/CICIDS2017/processed/train_test_data.pkl"
        )

    print("Loading CICIDS2017 processed split...", flush=True)
    x_cic_tr, x_cic_te, y_cic_tr, y_cic_te = joblib.load(CICIDS_PKL)
    x_cic_tr = np.asarray(x_cic_tr)
    x_cic_te = np.asarray(x_cic_te)
    y_cic_tr_bin = cicids_labels_to_binary(y_cic_tr)
    y_cic_te_bin = cicids_labels_to_binary(y_cic_te)
    x_cic_tr_a = cicids_matrix_to_aligned(x_cic_tr)
    x_cic_te_a = cicids_matrix_to_aligned(x_cic_te)

    print("Loading UNSW-NB15 official splits...", flush=True)
    unsw = load_unsw_nb15_splits(PROJECT_ROOT)
    x_unsw_tr_df, y_unsw_tr = unsw.x_train, unsw.y_train
    x_unsw_te_df, y_unsw_te = unsw.x_test, unsw.y_test
    if max_train or max_test:
        x_unsw_tr_df, y_unsw_tr = _maybe_subsample(x_unsw_tr_df, y_unsw_tr, max_train, 42)
        x_unsw_te_df, y_unsw_te = _maybe_subsample(x_unsw_te_df, y_unsw_te, max_test, 0)

    x_unsw_tr_a = unsw_frame_to_aligned(x_unsw_tr_df)
    x_unsw_te_a = unsw_frame_to_aligned(x_unsw_te_df)
    y_unsw_tr_bin = unsw_labels_to_binary(y_unsw_tr)
    y_unsw_te_bin = unsw_labels_to_binary(y_unsw_te)

    x_cic_tr_a, y_cic_tr_bin = _subsample_xy(x_cic_tr_a, y_cic_tr_bin, max_train, 42)
    x_cic_te_a, y_cic_te_bin = _subsample_xy(x_cic_te_a, y_cic_te_bin, max_test, 0)

    # In-domain controls (same aligned space) for context — not production metrics.
    in_domain = [
        _run_transfer(
            "cicids_aligned_in_domain",
            x_cic_tr_a,
            y_cic_tr_bin,
            x_cic_te_a,
            y_cic_te_bin,
            args.n_estimators,
        ),
        _run_transfer(
            "unsw_aligned_in_domain",
            x_unsw_tr_a,
            y_unsw_tr_bin,
            x_unsw_te_a,
            y_unsw_te_bin,
            args.n_estimators,
        ),
    ]

    transfers = [
        _run_transfer(
            "cicids_to_unsw",
            x_cic_tr_a,
            y_cic_tr_bin,
            x_unsw_te_a,
            y_unsw_te_bin,
            args.n_estimators,
        ),
        _run_transfer(
            "unsw_to_cicids",
            x_unsw_tr_a,
            y_unsw_tr_bin,
            x_cic_te_a,
            y_cic_te_bin,
            args.n_estimators,
        ),
    ]

    payload = {
        "experiment": "Phase 4 cross-dataset evaluation",
        "phase": 4,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": "binary_normal_vs_attack",
        "aligned_feature_count": len(ALIGNED_FEATURES),
        "aligned_features": shared_feature_names(),
        "alignment": alignment_documentation(),
        "n_estimators": args.n_estimators,
        "class_weight": "balanced_subsample",
        "quick_run": bool(args.quick or max_train or max_test),
        "official_splits_note": (
            "CICIDS uses processed train_test_data.pkl; UNSW uses official train/test CSVs. "
            "Scaler/imputer fit on source train only."
        ),
        "in_domain_controls": in_domain,
        "transfers": transfers,
        "comparison_table": [
            {
                "setting": row["name"],
                "attack_recall": row["metrics"]["attack_recall"],
                "false_positive_rate": row["metrics"]["false_positive_rate"],
                "false_negative_rate": row["metrics"]["false_negative_rate"],
                "roc_auc": row["metrics"]["roc_auc"],
                "pr_auc": row["metrics"]["pr_auc"],
                "f1_attack": row["metrics"]["f1_attack"],
                "accuracy": row["metrics"]["accuracy"],
            }
            for row in in_domain + transfers
        ],
        "research_focus": {
            "question": (
                "Does a carefully aligned numeric feature space transfer between "
                "CICIDS2017 and UNSW-NB15 for binary attack detection?"
            ),
            "interpretation_guide": (
                "Large drops from in-domain to transfer performance indicate limited "
                "cross-dataset generalization even after alignment — a scientifically "
                "useful negative/qualified result for the SOC pipeline narrative."
            ),
        },
        "notes": [
            "This IS a cross-dataset experiment, unlike Phases 1–3.",
            "Alignment is approximate; collectors and feature definitions differ.",
            "Does not replace production CICIDS Random Forest or change /analyze.",
            "Production DQN / risk / CTI stack is unchanged.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\nWrote {OUT_JSON}", flush=True)

    print("\n=== Phase 4 summary ===")
    print(f"{'setting':<28} {'AR':>7} {'FPR':>7} {'AUC':>7} {'F1':>7}")
    for row in payload["comparison_table"]:
        print(
            f"{row['setting']:<28} "
            f"{row['attack_recall']:>7.4f} "
            f"{row['false_positive_rate']:>7.4f} "
            f"{(row['roc_auc'] or 0):>7.4f} "
            f"{row['f1_attack']:>7.4f}"
        )


if __name__ == "__main__":
    main()
