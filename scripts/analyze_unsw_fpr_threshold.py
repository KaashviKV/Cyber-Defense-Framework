"""
UNSW-NB15 classifier FPR reduction via attack-probability thresholding.

Uses the existing saved UNSW Random Forest(s). Does NOT retrain, and does NOT
touch production CICIDS2017 models or /analyze.

Idea:
  P(attack) from the model; predict attack iff P(attack) >= threshold.
  Raising the threshold typically lowers FPR and may lower attack recall.

Usage:
  python scripts/analyze_unsw_fpr_threshold.py
  python scripts/analyze_unsw_fpr_threshold.py --quick
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.unsw_nb15 import UNSW_BENIGN_LABEL, load_unsw_nb15_splits  # noqa: E402
from scripts.evaluate_unsw_nb15 import _maybe_subsample  # noqa: E402

OUT_JSON = PROJECT_ROOT / "ml" / "saved_models" / "unsw_nb15_fpr_threshold.json"
MULTI_MODEL = PROJECT_ROOT / "ml" / "saved_models" / "random_forest_unsw_nb15.pkl"
BINARY_MODEL = PROJECT_ROOT / "ml" / "saved_models" / "random_forest_unsw_nb15_binary.pkl"

DEFAULT_THRESHOLDS = [
    0.30,
    0.40,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90,
]


def attack_scores_multiclass(model, x) -> np.ndarray:
    proba = model.predict_proba(x)
    classes = [str(c) for c in model.classes_]
    if UNSW_BENIGN_LABEL not in classes:
        return np.ones(len(x), dtype=float)
    return 1.0 - proba[:, classes.index(UNSW_BENIGN_LABEL)]


def attack_scores_binary(model, x) -> np.ndarray:
    proba = model.predict_proba(x)
    classes = [int(c) for c in model.classes_]
    idx = classes.index(1) if 1 in classes else len(classes) - 1
    return proba[:, idx]


def binary_rates(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> dict:
    yt = y_true_bin.astype(int)
    yp = y_pred_bin.astype(int)
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
        "accuracy": round(float(accuracy_score(yt, yp)), 4),
        "precision_attack": round(float(precision_score(yt, yp, zero_division=0)), 4),
        "f1_attack": round(float(f1_score(yt, yp, zero_division=0)), 4),
        "recall_attack": round(float(recall_score(yt, yp, zero_division=0)), 4),
    }


def evaluate_threshold(y_true_bin: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    y_pred = (scores >= threshold).astype(int)
    metrics = binary_rates(y_true_bin, y_pred)
    metrics["threshold"] = round(float(threshold), 4)
    return metrics


def choose_recommended(
    rows: list[dict],
    baseline_fpr: float,
    min_recall: float = 0.95,
) -> dict:
    """Prefer lowest FPR among rows that keep attack_recall >= min_recall."""
    eligible = [r for r in rows if (r["attack_recall"] or 0) >= min_recall]
    if eligible:
        best = min(eligible, key=lambda r: (r["false_positive_rate"], -r["attack_recall"]))
        rule = f"lowest FPR among thresholds with attack_recall >= {min_recall}"
    else:
        best = max(rows, key=lambda r: r["attack_recall"] or 0)
        rule = f"no threshold kept recall>={min_recall}; chose highest attack_recall"
    reduction = None
    if baseline_fpr and baseline_fpr > 0:
        reduction = round((baseline_fpr - best["false_positive_rate"]) / baseline_fpr, 4)
    return {
        "threshold": best["threshold"],
        "attack_recall": best["attack_recall"],
        "false_positive_rate": best["false_positive_rate"],
        "false_negative_rate": best["false_negative_rate"],
        "f1_attack": best["f1_attack"],
        "precision_attack": best["precision_attack"],
        "fpr_reduction_vs_baseline": reduction,
        "rule": rule,
        "min_recall_constraint": min_recall,
    }


def sweep_model(
    name: str,
    scores: np.ndarray,
    y_true_bin: np.ndarray,
    thresholds: list[float],
    baseline_threshold: float,
    min_recall: float,
) -> dict:
    baseline = evaluate_threshold(y_true_bin, scores, baseline_threshold)
    rows = [evaluate_threshold(y_true_bin, scores, t) for t in thresholds]
    # Ensure baseline threshold appears in the table.
    if not any(abs(r["threshold"] - baseline_threshold) < 1e-9 for r in rows):
        rows.append(baseline)
        rows.sort(key=lambda r: r["threshold"])
    recommended = choose_recommended(rows, baseline["false_positive_rate"], min_recall)
    return {
        "model": name,
        "score_definition": (
            "1 - P(Normal)" if "multiclass" in name else "P(Attack)"
        ),
        "baseline_threshold": baseline_threshold,
        "baseline": baseline,
        "threshold_curve": rows,
        "recommended": recommended,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="UNSW FPR threshold sweep")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-test", type=int, default=None)
    parser.add_argument("--min-recall", type=float, default=0.95)
    parser.add_argument(
        "--baseline-threshold",
        type=float,
        default=0.5,
        help="Reference decision threshold (default 0.5).",
    )
    args = parser.parse_args()

    max_test = args.max_test if args.max_test is not None else (4000 if args.quick else None)

    if not MULTI_MODEL.exists():
        raise FileNotFoundError(
            f"Missing {MULTI_MODEL}. Run python scripts/evaluate_unsw_nb15.py first."
        )

    print("Loading UNSW-NB15 test split...", flush=True)
    splits = load_unsw_nb15_splits(PROJECT_ROOT)
    x_test, y_test = splits.x_test, splits.y_test
    if max_test:
        x_test, y_test = _maybe_subsample(x_test, y_test, max_test, seed=0)
    y_true_bin = (np.asarray(y_test).astype(str) != UNSW_BENIGN_LABEL).astype(int)
    print(f"  test={x_test.shape} attacks={int(y_true_bin.sum())} benign={int((1-y_true_bin).sum())}")

    results = []

    print(f"Loading multiclass model {MULTI_MODEL}...", flush=True)
    multi = joblib.load(MULTI_MODEL)
    multi_scores = attack_scores_multiclass(multi, x_test)
    # Also report argmax collapse baseline (current Phase-1 style).
    y_pred_cls = np.asarray(multi.predict(x_test)).astype(str)
    argmax_bin = (y_pred_cls != UNSW_BENIGN_LABEL).astype(int)
    argmax_metrics = binary_rates(y_true_bin, argmax_bin)

    multi_block = sweep_model(
        "multiclass_rf_unsw",
        multi_scores,
        y_true_bin,
        DEFAULT_THRESHOLDS,
        args.baseline_threshold,
        args.min_recall,
    )
    multi_block["argmax_collapse_baseline"] = {
        **argmax_metrics,
        "note": "Predict attack if argmax class != Normal (previous default reporting style).",
    }
    results.append(multi_block)
    print(
        f"  multiclass baseline@{args.baseline_threshold}: "
        f"AR={multi_block['baseline']['attack_recall']} "
        f"FPR={multi_block['baseline']['false_positive_rate']}"
    )
    print(
        f"  multiclass recommended@{multi_block['recommended']['threshold']}: "
        f"AR={multi_block['recommended']['attack_recall']} "
        f"FPR={multi_block['recommended']['false_positive_rate']} "
        f"FPR_reduction={multi_block['recommended']['fpr_reduction_vs_baseline']}"
    )

    if BINARY_MODEL.exists():
        print(f"Loading binary model {BINARY_MODEL}...", flush=True)
        binary = joblib.load(BINARY_MODEL)
        bin_scores = attack_scores_binary(binary, x_test)
        bin_block = sweep_model(
            "binary_rf_unsw",
            bin_scores,
            y_true_bin,
            DEFAULT_THRESHOLDS,
            args.baseline_threshold,
            args.min_recall,
        )
        results.append(bin_block)
        print(
            f"  binary recommended@{bin_block['recommended']['threshold']}: "
            f"AR={bin_block['recommended']['attack_recall']} "
            f"FPR={bin_block['recommended']['false_positive_rate']} "
            f"FPR_reduction={bin_block['recommended']['fpr_reduction_vs_baseline']}"
        )
    else:
        print("Binary UNSW model not found; skipping binary sweep.", flush=True)

    # Prefer the model/threshold with lowest FPR under recall constraint.
    candidates = [r["recommended"] | {"model": r["model"]} for r in results]
    overall = min(
        candidates,
        key=lambda r: (r["false_positive_rate"], -r["attack_recall"]),
    )

    payload = {
        "experiment": "UNSW-NB15 FPR threshold analysis",
        "dataset": "UNSW-NB15",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_rows": int(len(y_true_bin)),
        "quick_run": bool(args.quick or max_test),
        "min_recall_constraint": args.min_recall,
        "baseline_threshold": args.baseline_threshold,
        "models": results,
        "overall_recommendation": overall,
        "comparison_table": [
            {
                "model": m["model"],
                "setting": "argmax_collapse" if "argmax_collapse_baseline" in m else None,
                "threshold": None,
                "attack_recall": m.get("argmax_collapse_baseline", {}).get("attack_recall"),
                "false_positive_rate": m.get("argmax_collapse_baseline", {}).get(
                    "false_positive_rate"
                ),
            }
            for m in results
            if "argmax_collapse_baseline" in m
        ]
        + [
            {
                "model": m["model"],
                "setting": f"threshold={row['threshold']}",
                "threshold": row["threshold"],
                "attack_recall": row["attack_recall"],
                "false_positive_rate": row["false_positive_rate"],
                "false_negative_rate": row["false_negative_rate"],
                "precision_attack": row["precision_attack"],
                "f1_attack": row["f1_attack"],
            }
            for m in results
            for row in m["threshold_curve"]
        ],
        "research_focus": {
            "question": (
                "Can raising the attack-probability threshold reduce classifier FPR "
                "while keeping attack recall high?"
            ),
            "note": (
                "This changes the detector decision rule only. It does not use CTI/DQN. "
                "Operational response policies are a separate experiment."
            ),
        },
        "notes": [
            "Does not modify production CICIDS2017 random_forest_model.pkl.",
            "Does not modify /analyze or production DQN.",
            "Uses saved UNSW-only models under ml/saved_models/.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\nWrote {OUT_JSON}", flush=True)
    print(
        f"Overall: {overall['model']} @ {overall['threshold']} "
        f"AR={overall['attack_recall']} FPR={overall['false_positive_rate']} "
        f"reduction={overall.get('fpr_reduction_vs_baseline')}"
    )


if __name__ == "__main__":
    main()
