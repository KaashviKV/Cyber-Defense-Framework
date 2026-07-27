import os
import sys

# --------------------------------------------------
# Add backend folder to Python path
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.append(BACKEND_PATH)

# --------------------------------------------------
# Import configuration
# --------------------------------------------------

from config.risk_config import (
    ATTACK_WEIGHT,
    CONFIDENCE_WEIGHT,
    VIRUSTOTAL_WEIGHT,
    ABUSEIPDB_WEIGHT,
    ATTACK_SEVERITY,
    SAFE_THRESHOLD,
    LOW_THRESHOLD,
    MEDIUM_THRESHOLD,
    HIGH_THRESHOLD,
)


class RiskEngine:

    def calculate_risk(
        self,
        attack_name,
        model_confidence,
        virustotal_score,
        abuse_score,
    ):

        # Attack severity from configuration
        attack_score = ATTACK_SEVERITY.get(attack_name, 50)

        # Weighted Risk Score
        risk_score = (
            attack_score * ATTACK_WEIGHT
            + model_confidence * CONFIDENCE_WEIGHT
            + virustotal_score * VIRUSTOTAL_WEIGHT
            + abuse_score * ABUSEIPDB_WEIGHT
        )

        # Determine Risk Level
        risk_level = self.get_risk_level(risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level
        }

    def get_risk_level(self, score):

        if score < SAFE_THRESHOLD:
            return "SAFE"

        elif score < LOW_THRESHOLD:
            return "LOW"

        elif score < MEDIUM_THRESHOLD:
            return "MEDIUM"

        elif score < HIGH_THRESHOLD:
            return "HIGH"

        else:
            return "CRITICAL"


# --------------------------------------------------
# Testing
# --------------------------------------------------

if __name__ == "__main__":

    engine = RiskEngine()

    result = engine.calculate_risk(
        attack_name="DDoS",
        model_confidence=96,
        virustotal_score=85,
        abuse_score=90,
    )

    print("\nCalculated Risk")
    print(result)