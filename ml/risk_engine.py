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


def normalize_virustotal_score(vt_result):
    """
    Convert VirusTotal last_analysis_stats into a 0-100 score.

    Malicious detections count fully; suspicious detections count half.
    Falls back to 0 when the API response is missing or failed.
    """
    if not isinstance(vt_result, dict) or "error" in vt_result:
        return 0.0

    malicious = float(vt_result.get("malicious", 0) or 0)
    suspicious = float(vt_result.get("suspicious", 0) or 0)
    harmless = float(vt_result.get("harmless", 0) or 0)
    undetected = float(vt_result.get("undetected", 0) or 0)

    total = malicious + suspicious + harmless + undetected
    if total <= 0:
        return 0.0

    score = ((malicious + (0.5 * suspicious)) / total) * 100
    return round(min(100.0, max(0.0, score)), 2)


def _effective_attack_score(
    attack_name: str,
    attack_score: float,
    virustotal_score: float,
    abuse_score: float,
) -> float:
    """
    When ML classifies traffic as BENIGN but CTI flags the IP,
    incorporate reputation so malicious IPs are not scored as LOW/SAFE.
    """
    reputation_floor = max(virustotal_score, abuse_score)
    return max(attack_score, reputation_floor)


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

        # Clamp CTI / confidence inputs onto a shared 0-100 scale
        model_confidence = float(min(100.0, max(0.0, model_confidence)))
        virustotal_score = float(min(100.0, max(0.0, virustotal_score)))
        abuse_score = float(min(100.0, max(0.0, abuse_score)))

        effective_attack_score = _effective_attack_score(
            attack_name,
            float(attack_score),
            virustotal_score,
            abuse_score,
        )

        # Weighted Risk Score
        risk_score = (
            effective_attack_score * ATTACK_WEIGHT
            + model_confidence * CONFIDENCE_WEIGHT
            + virustotal_score * VIRUSTOTAL_WEIGHT
            + abuse_score * ABUSEIPDB_WEIGHT
        )

        # Determine Risk Level
        risk_level = self.get_risk_level(risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "attack_score_used": round(effective_attack_score, 2),
            "cti_reputation_boost": effective_attack_score > float(attack_score),
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