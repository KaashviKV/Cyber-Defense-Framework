"""
AI Decision Engine

Uses the trained Deep Q Network to select the best defensive response.
Backward compatible: CTI/confidence arguments are optional.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
sys.path.append(PROJECT_ROOT)

from ml.fail_safe import apply_fail_safe
from ml.rl.explain_action import explain_rl_decision
from ml.rl.predict_action import RLDecisionMaker
from ml.response_engine.response_actions import (
    allow_traffic,
    alert_admin,
    block_ip,
    isolate_host,
)


class DecisionEngine:
    def __init__(self) -> None:
        self.rl = RLDecisionMaker()

    def decide(
        self,
        ip_address: str,
        attack_severity: float,
        risk_score: float,
        confidence: float = 0.0,
        virustotal_score: float = 0.0,
        abuseipdb_score: float = 0.0,
        attack_name: str = "",
        risk_level: str = "",
        cti_status: str = "ok",
    ) -> dict[str, Any]:
        print("\n==============================")
        print("AI DECISION ENGINE")
        print("==============================")
        print(f"IP Address       : {ip_address}")
        print(f"Attack Severity  : {attack_severity}")
        print(f"Risk Score       : {risk_score}")
        print(f"Confidence       : {confidence}")
        print(f"VirusTotal Score : {virustotal_score}")
        print(f"AbuseIPDB Score  : {abuseipdb_score}")
        print(f"DQN Version      : {self.rl.model_version}")

        details = self.rl.predict_with_details(
            attack_severity,
            risk_score,
            confidence=confidence,
            virustotal_score=virustotal_score,
            abuseipdb_score=abuseipdb_score,
        )
        action = details["action"]
        action, fail_safe_applied, fail_safe_reason = apply_fail_safe(
            action, attack_name, cti_status
        )

        print(f"\nRecommended Action : {action}")

        simulation: dict[str, Any] = {"mode": "simulated", "action": action, "effects": []}
        if action == "NO_ACTION":
            simulation = allow_traffic(ip_address)
        elif action == "ALERT_ADMIN":
            simulation = alert_admin(ip_address, risk_score)
        elif action == "BLOCK_IP":
            simulation = block_ip(ip_address)
        elif action == "ISOLATE_HOST":
            simulation = isolate_host(ip_address)
        else:
            print("Unknown Action")

        explanation = explain_rl_decision(
            action=action,
            attack=attack_name,
            severity=attack_severity,
            confidence=confidence,
            risk_score=risk_score,
            risk_level=risk_level,
            virustotal_score=virustotal_score,
            abuseipdb_score=abuseipdb_score,
            q_values=details.get("q_values"),
            model_version=self.rl.model_version,
        )

        return {
            "ip": ip_address,
            "action": action,
            "risk_score": risk_score,
            "status": "SUCCESS",
            "rl_model_version": self.rl.model_version,
            "rl_state_size": self.rl.state_size,
            "q_values": details.get("q_values"),
            "simulation": simulation,
            "explanation": explanation,
            "fail_safe_applied": fail_safe_applied,
            "fail_safe_reason": fail_safe_reason,
            "policy_action": details["action"],
        }


if __name__ == "__main__":
    engine = DecisionEngine()
    engine.decide(
        ip_address="192.168.1.10",
        attack_severity=95,
        risk_score=92,
        confidence=96,
        virustotal_score=80,
        abuseipdb_score=90,
    )
