"""Load experiment JSON artifacts for the dashboard (no retraining)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.config.config import PROJECT_ROOT

SAVED = PROJECT_ROOT / "ml" / "saved_models"

ARTIFACTS = {
    "ml_model_comparison": SAVED / "ml_model_comparison.json",
    "response_ablation": SAVED / "ablation_results.json",
    "pipeline_ablation": SAVED / "pipeline_ablation.json",
    "dqn_vs_double_dqn": SAVED / "dqn_vs_double_dqn.json",
    "case_studies": SAVED / "case_study_results.json",
    "evolving_threats": SAVED / "evolving_threat_results.json",
    "risk_engine": SAVED / "risk_engine_evaluation.json",
    "robustness": SAVED / "robustness_results.json",
    "sequential_rl": SAVED / "sequential_rl_results.json",
    "unsw_nb15_evaluation": SAVED / "unsw_nb15_evaluation.json",
    "unsw_nb15_phase1": SAVED / "unsw_nb15_phase1_analysis.json",
    "unsw_nb15_phase2": SAVED / "unsw_nb15_phase2_imbalance.json",
    "unsw_nb15_phase3": SAVED / "unsw_nb15_phase3_feature_ablation.json",
    "cross_dataset_phase4": SAVED / "cross_dataset_phase4.json",
    "unsw_nb15_fpr_threshold": SAVED / "unsw_nb15_fpr_threshold.json",
}


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "message": f"Run the matching script to generate {path.name}.",
            "path": str(path),
        }
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {"status": "ok", "path": str(path), "data": data}


def get_experiments_payload() -> dict[str, Any]:
    return {
        "status": "success",
        "experiments": {name: _read(path) for name, path in ARTIFACTS.items()},
        "how_to_run": {
            "ml_comparison": "python scripts/compare_ml_models.py",
            "response_ablation": "python scripts/evaluate_rl_ablation.py",
            "pipeline_ablation": "python scripts/evaluate_pipeline_ablation.py",
            "dqn_vs_double_dqn": "python -m ml.rl.train_compare_agents",
            "case_studies": "python scripts/evaluate_case_studies.py",
            "evolving_threats": "python scripts/evaluate_evolving_threats.py",
            "risk_engine": "python scripts/evaluate_risk_weights.py",
            "robustness": "python scripts/evaluate_robustness.py --synthetic",
            "unsw_nb15": "python scripts/evaluate_unsw_nb15.py",
            "unsw_nb15_phase1": "python scripts/analyze_unsw_nb15_phase1.py",
            "unsw_nb15_phase2": "python scripts/analyze_unsw_nb15_phase2.py",
            "unsw_nb15_phase3": "python scripts/analyze_unsw_nb15_phase3.py",
            "cross_dataset_phase4": "python scripts/analyze_cross_dataset_phase4.py",
            "unsw_nb15_fpr_threshold": "python scripts/analyze_unsw_fpr_threshold.py",
            "all": "python -m experiments.run_all --quick",
        },
    }
