"""
====================================================
Intelligent Cyber Defense Framework
Main Integration Pipeline

Pipeline Flow

1. Random Forest Prediction
2. VirusTotal Threat Intelligence
3. AbuseIPDB Reputation Check
4. Risk Engine
5. Reinforcement Learning Decision Engine
6. Final Security Report
====================================================
"""

import os
import sys
import numpy as np
from backend.models.analysis_model import save_analysis

# ----------------------------------------------------
# Add Project Root
# ----------------------------------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PROJECT_ROOT)

# ----------------------------------------------------
# Imports
# ----------------------------------------------------

from ml.predict import predict_attack
from cti.virustotal import check_virustotal
from cti.abuseipdb import check_abuseip
from ml.risk_engine import RiskEngine
from ml.response_engine.decision_engine import DecisionEngine


class CyberDefensePipeline:

    def __init__(self):

        self.risk_engine = RiskEngine()
        self.decision_engine = DecisionEngine()

    # ------------------------------------------------

    def analyze(self, features, ip_address):

        print("\n===================================")
        print("STEP 1 : RANDOM FOREST PREDICTION")
        print("===================================")

        prediction = predict_attack(features)

        print(prediction)

        attack = prediction["attack"]
        severity = prediction["severity"]
        confidence = prediction["confidence"]

        # ------------------------------------------------

        print("\n===================================")
        print("STEP 2 : VIRUSTOTAL")
        print("===================================")

        vt = check_virustotal(ip_address)

        print(vt)

        vt_score = vt.get("malicious", 0)

        # ------------------------------------------------

        print("\n===================================")
        print("STEP 3 : ABUSEIPDB")
        print("===================================")

        abuse = check_abuseip(ip_address)

        print(abuse)

        abuse_score = abuse.get("abuse_confidence", 0)

        # ------------------------------------------------

        print("\n===================================")
        print("STEP 4 : RISK ENGINE")
        print("===================================")

        risk = self.risk_engine.calculate_risk(

            attack_name=attack,

            model_confidence=confidence,

            virustotal_score=vt_score,

            abuse_score=abuse_score
        )

        print(risk)

        # ------------------------------------------------

        print("\n===================================")
        print("STEP 5 : RL DECISION ENGINE")
        print("===================================")

        decision = self.decision_engine.decide(

            ip_address=ip_address,

            attack_severity=severity,

            risk_score=risk["risk_score"]

        )

        # ------------------------------------------------

        print("\n===================================")
        print("FINAL REPORT")
        print("===================================")

        result = {

            "ip_address": ip_address,

            "prediction": prediction,

            "virustotal": vt,

            "abuseipdb": abuse,

            "risk": risk,

            "decision": decision

        }

        analysis_id = save_analysis(report)

        print("\nSaved to MongoDB")

        print("Document ID :", analysis_id)

        return result


# ----------------------------------------------------
# Testing
# ----------------------------------------------------

if __name__ == "__main__":

    pipeline = CyberDefensePipeline()

    print("\nCreating Dummy Network Traffic...\n")

    dummy_features = np.random.rand(78)

    ip = input("Enter IP Address : ")

    report = pipeline.analyze(

        features=dummy_features,

        ip_address=ip

    )

    print("\n===================================")
    print("PIPELINE COMPLETED")
    print("===================================\n")

    from pprint import pprint

    pprint(report)
    