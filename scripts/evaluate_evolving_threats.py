"""
Evolving / unseen-attack evaluation.

1) Leave-one-attack-class-out: train without one class, test on that class (generalization).
2) Distribution shift: train on a benign-heavy mix, test on an attack-heavy mix.

  python scripts/evaluate_evolving_threats.py
  python scripts/evaluate_evolving_threats.py --synthetic
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "dataset" / "CICIDS2017" / "processed" / "train_test_data.pkl"
OUT_PATH = PROJECT_ROOT / "ml" / "saved_models" / "evolving_threat_results.json"


def _security(y_true, y_pred, benign) -> dict:
    yt = np.array(y_true)
    yp = np.array(y_pred)
    attack = yt != benign
    benign_mask = yt == benign
    pred_attack = yp != benign
    return {
        "precision_weighted": round(float(precision_score(yt, yp, average="weighted", zero_division=0)), 4),
        "recall_weighted": round(float(recall_score(yt, yp, average="weighted", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4),
        "detection_rate": round(float(np.mean(pred_attack[attack])) if attack.any() else 0.0, 4),
        "false_positive_rate": round(float(np.mean(pred_attack[benign_mask])) if benign_mask.any() else 0.0, 4),
        "false_negative_rate": round(float(np.mean(~pred_attack[attack])) if attack.any() else 0.0, 4),
    }


def _load(synthetic: bool):
    if synthetic:
        from sklearn.datasets import make_classification

        x, y = make_classification(
            n_samples=3000,
            n_features=78,
            n_informative=18,
            n_classes=6,
            n_clusters_per_class=1,
            random_state=7,
        )
        return np.asarray(x), np.asarray(y), 0, True

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}. Pass --synthetic for a smoke run.")

    import joblib

    x_train, x_test, y_train, y_test = joblib.load(DATA_PATH)
    x = np.concatenate([np.asarray(x_train), np.asarray(x_test)])
    y = np.concatenate([np.asarray(y_train), np.asarray(y_test)])
    unique = list(np.unique(y))
    benign = 0 if 0 in unique else unique[0]
    for candidate in ("BENIGN", "Benign"):
        if candidate in unique:
            benign = candidate
            break
    rng = np.random.default_rng(42)
    if len(y) > 40000:
        idx = rng.choice(len(y), size=40000, replace=False)
        x, y = x[idx], y[idx]
    return x, y, benign, False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()

    x, y, benign, synthetic = _load(args.synthetic)
    classes = [c for c in np.unique(y) if c != benign]
    holdouts = list(classes[: min(4, len(classes))])

    unseen_rows = []
    for holdout in holdouts:
        train_mask = y != holdout
        test_mask = y == holdout
        if test_mask.sum() < 20 or train_mask.sum() < 50:
            continue
        clf = RandomForestClassifier(n_estimators=60, random_state=42, n_jobs=-1)
        clf.fit(x[train_mask], y[train_mask])
        pred = clf.predict(x[test_mask])
        unseen_recall = float(np.mean(pred == holdout))
        mapped_as_attack = float(np.mean(pred != benign))
        unseen_rows.append({
            "held_out_class": str(holdout),
            "test_samples": int(test_mask.sum()),
            "exact_class_recall": round(unseen_recall, 4),
            "detected_as_any_attack": round(mapped_as_attack, 4),
            "note": (
                "Exact-class recall is expected to be low for a class never seen in training; "
                "detected_as_any_attack shows whether the IDS still flags it as non-benign."
            ),
        })

    # Distribution shift: train mostly benign, test mostly attacks
    rng = np.random.default_rng(1)
    benign_idx = np.where(y == benign)[0]
    attack_idx = np.where(y != benign)[0]
    n_train_b = min(len(benign_idx), 4000)
    n_train_a = min(len(attack_idx), 800)
    n_test_b = min(len(benign_idx) - n_train_b, 400)
    n_test_a = min(len(attack_idx) - n_train_a, 2500)

    tr = np.concatenate([
        rng.choice(benign_idx, n_train_b, replace=False),
        rng.choice(attack_idx, n_train_a, replace=False),
    ])
    remaining_b = np.setdiff1d(benign_idx, tr)
    remaining_a = np.setdiff1d(attack_idx, tr)
    te = np.concatenate([
        rng.choice(remaining_b, min(n_test_b, len(remaining_b)), replace=False) if len(remaining_b) else np.array([], dtype=int),
        rng.choice(remaining_a, min(n_test_a, len(remaining_a)), replace=False) if len(remaining_a) else np.array([], dtype=int),
    ])

    static = RandomForestClassifier(n_estimators=60, random_state=42, n_jobs=-1)
    static.fit(x[tr], y[tr])
    shift_metrics = _security(y[te], static.predict(x[te]), benign)

    iid_split = int(0.7 * len(y))
    perm = rng.permutation(len(y))
    iid_clf = RandomForestClassifier(n_estimators=60, random_state=42, n_jobs=-1)
    iid_clf.fit(x[perm[:iid_split]], y[perm[:iid_split]])
    iid_metrics = _security(y[perm[iid_split:]], iid_clf.predict(x[perm[iid_split:]]), benign)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "synthetic_smoke" if synthetic else "CICIDS2017",
        "static_iid": iid_metrics,
        "evolving_attack_heavy_test": shift_metrics,
        "unseen_class_holdout": unseen_rows,
        "interpretation": (
            "Static IID performance is an optimistic bound. Attack-heavy shift and unseen-class "
            "holdout show how a frozen IDS degrades — motivation for CTI + RL adaptation rather "
            "than accuracy on a random split alone."
        ),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== Evolving / Unseen Threats ===")
    print("IID:", iid_metrics)
    print("Shift:", shift_metrics)
    for row in unseen_rows:
        print(f"Holdout {row['held_out_class']}: exact={row['exact_class_recall']} any-attack={row['detected_as_any_attack']}")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
