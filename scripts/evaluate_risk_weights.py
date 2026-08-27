"""Show that CTI + ML produces wider, more useful risk differentiation than ML-only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.risk_engine import RiskEngine

CASES = [
    {"name": "Clean benign", "attack": "BENIGN", "confidence": 90, "vt": 1, "abuse": 0, "reports": 0},
    {"name": "Benign ML + malicious IP", "attack": "BENIGN", "confidence": 51, "vt": 15, "abuse": 100, "reports": 4000},
    {"name": "PortScan modest CTI", "attack": "PortScan", "confidence": 70, "vt": 10, "abuse": 25, "reports": 12},
    {"name": "DDoS + hot CTI", "attack": "DDoS", "confidence": 96, "vt": 70, "abuse": 85, "reports": 200},
    {"name": "DDoS + clean CTI", "attack": "DDoS", "confidence": 91, "vt": 2, "abuse": 4, "reports": 0},
    {"name": "Whitelisted resolver", "attack": "BENIGN", "confidence": 88, "vt": 0, "abuse": 5, "reports": 2, "whitelisted": True},
]


def ml_only_score(attack: str, confidence: float) -> float:
    from config.risk_config import ATTACK_SEVERITY

    return 0.40 * ATTACK_SEVERITY.get(attack, 50) + 0.20 * confidence


def main() -> None:
    engine = RiskEngine()
    rows = []
    for case in CASES:
        fused = engine.calculate_risk(
            attack_name=case["attack"],
            model_confidence=case["confidence"],
            virustotal_score=case["vt"],
            abuse_score=case["abuse"],
            total_reports=case.get("reports", 0),
            is_whitelisted=case.get("whitelisted", False),
        )
        ml = ml_only_score(case["attack"], case["confidence"])
        rows.append({
            "case": case["name"],
            "ml_only_partial_score": round(ml, 2),
            "fused_risk_score": fused["risk_score"],
            "fused_risk_level": fused["risk_level"],
            "cti_reputation_boost": fused["cti_reputation_boost"],
        })

    scores = [r["fused_risk_score"] for r in rows]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weights": "attack 0.40, confidence 0.20, VirusTotal 0.20, AbuseIPDB 0.20",
        "justification": (
            "Severity is the largest term because known high-impact CICIDS classes "
            "(DDoS, Infiltration, Heartbleed) should dominate. CTI jointly equals "
            "severity so a weak BENIGN label cannot hide a hot reputation. Confidence "
            "is a stabilizer. Report volume is blended into AbuseIPDB; whitelist scales CTI."
        ),
        "fused_score_range": {"min": min(scores), "max": max(scores), "spread": round(max(scores) - min(scores), 2)},
        "results": rows,
    }
    out = PROJECT_ROOT / "ml" / "saved_models" / "risk_engine_evaluation.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
