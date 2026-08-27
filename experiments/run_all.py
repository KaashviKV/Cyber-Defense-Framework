"""Reproduce the fast experiment suite without retraining production models."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stderr_tail": (proc.stderr or "")[-500:],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--unsw",
        action="store_true",
        help="Also run standalone UNSW-NB15 IDS evaluation (can be slow on full data).",
    )
    parser.add_argument(
        "--unsw-quick",
        action="store_true",
        help="Run a subsampled UNSW-NB15 smoke evaluation.",
    )
    args = parser.parse_args()
    python = sys.executable
    jobs = [
        [python, "scripts/evaluate_risk_weights.py"],
        [python, "scripts/evaluate_robustness.py", "--synthetic"],
        [python, "scripts/evaluate_pipeline_ablation.py"],
        [python, "scripts/evaluate_case_studies.py"],
    ]
    if not args.quick:
        jobs.extend([
            [python, "scripts/evaluate_rl_ablation.py"],
            [python, "scripts/evaluate_sequential_rl.py"],
            [python, "scripts/compare_ml_models.py", "--synthetic", "--quick"],
        ])
    if args.unsw_quick:
        jobs.append([python, "scripts/evaluate_unsw_nb15.py", "--quick"])
    elif args.unsw:
        jobs.append([python, "scripts/evaluate_unsw_nb15.py"])
    results = [_run(cmd) for cmd in jobs]
    out_dir = PROJECT_ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "experiment_id": f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jobs": results,
    }
    path = out_dir / "run_all.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    if any(not row["ok"] for row in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
