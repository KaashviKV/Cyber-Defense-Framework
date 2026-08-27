"""
Case-study evaluation for conference demos.

Compares rule-based, legacy DQN, and CTI-aware DQN on fixed scenarios
without calling external APIs.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.rl.baselines import rule_based_action
from ml.rl.predict_action import RLDecisionMaker

CASES = [
    {
        "name": "Benign DNS resolver",
        "ip": "8.8.8.8",
        "state": {
            "attack": "BENIGN",
            "severity": 0,
            "confidence": 85,
            "risk_score": 12,
            "virustotal_score": 1,
            "abuseipdb_score": 0,
        },
    },
    {
        "name": "High-abuse Tor exit (BENIGN ML + hot CTI)",
        "ip": "185.220.101.1",
        "state": {
            "attack": "BENIGN",
            "severity": 0,
            "confidence": 51,
            "risk_score": 73,
            "virustotal_score": 15,
            "abuseipdb_score": 100,
        },
    },
    {
        "name": "Classic DDoS",
        "ip": "203.0.113.50",
        "state": {
            "attack": "DDoS",
            "severity": 95,
            "confidence": 96,
            "risk_score": 88,
            "virustotal_score": 40,
            "abuseipdb_score": 70,
        },
    },
    {
        "name": "Port scan medium risk",
        "ip": "198.51.100.20",
        "state": {
            "attack": "PortScan",
            "severity": 60,
            "confidence": 70,
            "risk_score": 48,
            "virustotal_score": 10,
            "abuseipdb_score": 25,
        },
    },
    {
        "name": "Infiltration critical",
        "ip": "203.0.113.99",
        "state": {
            "attack": "Infiltration",
            "severity": 98,
            "confidence": 92,
            "risk_score": 94,
            "virustotal_score": 75,
            "abuseipdb_score": 88,
        },
    },
    {
        "name": "Low-risk Bot",
        "ip": "198.51.100.40",
        "state": {
            "attack": "Bot",
            "severity": 55,
            "confidence": 62,
            "risk_score": 38,
            "virustotal_score": 8,
            "abuseipdb_score": 12,
        },
    },
    {
        "name": "Conflicting CTI (DDoS ML, clean reputation)",
        "ip": "203.0.113.8",
        "state": {
            "attack": "DDoS",
            "severity": 95,
            "confidence": 91,
            "risk_score": 58,
            "virustotal_score": 2,
            "abuseipdb_score": 5,
        },
    },
]


def predict_all(state: dict, current: RLDecisionMaker, legacy: RLDecisionMaker | None) -> dict:
    rule = rule_based_action(state)
    v2 = current.predict(
        state["severity"],
        state["risk_score"],
        confidence=state["confidence"],
        virustotal_score=state["virustotal_score"],
        abuseipdb_score=state["abuseipdb_score"],
    )
    v1 = None
    if legacy is not None:
        v1 = legacy.predict(state["severity"], state["risk_score"])
    return {
        "rule_based": rule,
        "dqn_v1_legacy": v1,
        "dqn_v2_cti": v2,
    }


def main() -> None:
    current = RLDecisionMaker()
    legacy_path = PROJECT_ROOT / "ml" / "saved_models" / "dqn_model_v1_legacy.pth"
    legacy = RLDecisionMaker(str(legacy_path)) if legacy_path.exists() else None

    rows = []
    for case in CASES:
        decisions = predict_all(case["state"], current, legacy)
        rows.append({
            "name": case["name"],
            "ip": case["ip"],
            "state": case["state"],
            "decisions": decisions,
        })

    metrics_path = PROJECT_ROOT / "ml" / "saved_models" / "dqn_training_metrics.json"
    learning_curve = None
    if metrics_path.exists():
        with open(metrics_path, encoding="utf-8") as fh:
            learning_curve = json.load(fh)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": current.model_version,
        "state_size": current.state_size,
        "cases": rows,
        "learning_curve_summary": {
            "episodes": learning_curve.get("episodes") if learning_curve else None,
            "avg_reward_last_50": learning_curve.get("avg_reward_last_50") if learning_curve else None,
            "reward_history": learning_curve.get("reward_history") if learning_curve else [],
        },
    }

    out = PROJECT_ROOT / "ml" / "saved_models" / "case_study_results.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print("\n=== Case Studies ===")
    for row in rows:
        d = row["decisions"]
        print(f"\n{row['name']} ({row['ip']})")
        print(f"  risk={row['state']['risk_score']} vt={row['state']['virustotal_score']} abuse={row['state']['abuseipdb_score']}")
        print(f"  rule={d['rule_based']} | v1={d['dqn_v1_legacy']} | v2={d['dqn_v2_cti']}")

    if learning_curve:
        print(f"\nLearning curve: episodes={learning_curve['episodes']}, avg_last_50={learning_curve['avg_reward_last_50']:.2f}")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
