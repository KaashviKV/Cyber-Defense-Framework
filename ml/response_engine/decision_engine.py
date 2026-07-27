"""
AI Decision Engine

This module uses the trained Deep Q Network
to select the best defensive response.
"""

import os
import sys

# -------------------------------------------------
# Project Root
# -------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

sys.path.append(PROJECT_ROOT)

# -------------------------------------------------
# RL Decision Maker
# -------------------------------------------------

from ml.rl.predict_action import RLDecisionMaker

# -------------------------------------------------
# Response Actions
# -------------------------------------------------

from ml.response_engine.response_actions import (
    allow_traffic,
    alert_admin,
    block_ip,
    isolate_host
)


class DecisionEngine:

    def __init__(self):

        self.rl = RLDecisionMaker()

    def decide(self,
               ip_address,
               attack_severity,
               risk_score):

        print("\n==============================")
        print("AI DECISION ENGINE")
        print("==============================")

        print(f"IP Address       : {ip_address}")
        print(f"Attack Severity  : {attack_severity}")
        print(f"Risk Score       : {risk_score}")

        action = self.rl.predict(
            attack_severity,
            risk_score
        )

        print(f"\nRecommended Action : {action}")

        if action == "NO_ACTION":

            allow_traffic(ip_address)

        elif action == "ALERT_ADMIN":

            alert_admin(ip_address, risk_score)

        elif action == "BLOCK_IP":

            block_ip(ip_address)

        elif action == "ISOLATE_HOST":

            isolate_host(ip_address)

        else:

            print("Unknown Action")

        return {
            "ip": ip_address,
            "action": action,
            "risk_score": risk_score,
            "status": "SUCCESS"
        }


# -------------------------------------------------
# Testing
# -------------------------------------------------

if __name__ == "__main__":

    engine = DecisionEngine()

    engine.decide(

        ip_address="192.168.1.10",

        attack_severity=95,

        risk_score=92
    )