"""
Pipeline-component ablation on fixed scenarios (ML vs CTI vs Risk vs RL).

Does not call external APIs. Writes ml/saved_models/pipeline_ablation.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.rl.baselines import ml_cti_action, ml_cti_risk_action, ml_only_action
from ml.rl.predict_action import RLDecisionMaker
from ml.risk_engine import RiskEngine
from scripts.evaluate_case_studies import CASES


def _risk_for(state: dict) -> dict:
    engine = RiskEngine()
    return engine.calculate_risk(
        attack_name=state.get("attack", "BENIGN"),
        model_confidence=state.get("confidence", 0),
        virustotal_score=state.get("virustotal_score", 0),
        abuse_score=state.get("abuseipdb_score", 0),
        total_reports=state.get("total_reports", 0),
        is_whitelisted=state.get("is_whitelisted", False),
    )


def main() -> None:
    rl = RLDecisionMaker()
    rows = []
    for case in CASES:
        state = dict(case["state"])
        risk = _risk_for(state)
        fused = {**state, "risk_score": risk["risk_score"]}
        dqn_action = rl.predict(
            fused["severity"],
            fused["risk_score"],
            confidence=fused.get("confidence", 0),
            virustotal_score=fused.get("virustotal_score", 0),
            abuseipdb_score=fused.get("abuseipdb_score", 0),
        )
        rows.append({
            "case": case["name"],
            "attack": state.get("attack"),
            "ml_only": ml_only_action(state),
            "ml_cti": ml_cti_action(state),
            "ml_cti_risk": ml_cti_risk_action(fused),
            "ml_cti_risk_dqn": dqn_action,
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "cti_reputation_boost": risk["cti_reputation_boost"],
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": "Does every component of the architecture change the response?",
        "results": rows,
    }
    out = PROJECT_ROOT / "ml" / "saved_models" / "pipeline_ablation.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== Pipeline Ablation (fixed cases) ===")
    print(f"{'Case':<40} {'ML':<14} {'+CTI':<14} {'+Risk':<14} {'+DQN':<14}")
    for row in rows:
        print(
            f"{row['case'][:39]:<40} {row['ml_only']:<14} {row['ml_cti']:<14} "
            f"{row['ml_cti_risk']:<14} {row['ml_cti_risk_dqn']:<14}"
        )
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
