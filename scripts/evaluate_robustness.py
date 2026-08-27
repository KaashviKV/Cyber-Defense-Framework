"""Perturb flow vectors and measure Random Forest label stability."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.predict import rf_model


def _flip_rate(x: np.ndarray, noise: float, rounds: int = 40) -> float:
    base = rf_model.predict(x)
    flips = 0
    rng = np.random.default_rng(0)
    for _ in range(rounds):
        perturb = x * (1.0 + rng.uniform(-noise, noise, size=x.shape))
        pred = rf_model.predict(perturb)
        flips += int(pred[0] != base[0])
    return round(flips / rounds, 4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    rng = np.random.default_rng(7)
    x = rng.random((1, 78))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "synthetic_vectors" if args.synthetic else "random_probe",
        "note": "Controlled feature noise on the production RF. Not an attack on a live network.",
        "results": {
            "noise_1pct": {"flip_rate": _flip_rate(x, 0.01)},
            "noise_5pct": {"flip_rate": _flip_rate(x, 0.05)},
            "noise_10pct": {"flip_rate": _flip_rate(x, 0.10)},
        },
    }
    out = PROJECT_ROOT / "ml" / "saved_models" / "robustness_results.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
