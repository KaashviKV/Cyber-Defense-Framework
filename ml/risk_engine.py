import math
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
    REPORTS_BLEND,
    WHITELIST_CTI_SCALE,
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


def normalize_report_score(total_reports) -> float:
    """Map report counts onto 0-100 with a log scale (1 report ~ 6, 100 ~ 40, 1000 ~ 60)."""
    try:
        reports = max(0.0, float(total_reports or 0))
    except (TypeError, ValueError):
        return 0.0
    if reports <= 0:
        return 0.0

    return round(min(100.0, 20.0 * math.log10(1.0 + reports)), 2)


class RiskEngine:

    def calculate_risk(
        self,
        attack_name,
        model_confidence,
        virustotal_score,
        abuse_score,
        total_reports=0,
        is_whitelisted=False,
        vt_freshness=1.0,
        abuse_freshness=1.0,
    ):

        # Attack severity from configuration
        attack_score = ATTACK_SEVERITY.get(attack_name, 50)

        # Clamp CTI / confidence inputs onto a shared 0-100 scale
        model_confidence = float(min(100.0, max(0.0, model_confidence)))
        virustotal_score = float(min(100.0, max(0.0, virustotal_score))) * float(vt_freshness)
        abuse_score = float(min(100.0, max(0.0, abuse_score))) * float(abuse_freshness)
        reports_score = normalize_report_score(total_reports)

        if is_whitelisted:
            virustotal_score *= WHITELIST_CTI_SCALE
            abuse_score *= WHITELIST_CTI_SCALE
            reports_score *= WHITELIST_CTI_SCALE

        abuse_effective = min(
            100.0,
            (1.0 - REPORTS_BLEND) * abuse_score + REPORTS_BLEND * max(abuse_score, reports_score),
        )

        effective_attack_score = _effective_attack_score(
            attack_name,
            float(attack_score),
            virustotal_score,
            abuse_effective,
        )

        attack_contrib = effective_attack_score * ATTACK_WEIGHT
        confidence_contrib = model_confidence * CONFIDENCE_WEIGHT
        vt_contrib = virustotal_score * VIRUSTOTAL_WEIGHT
        abuse_contrib = abuse_effective * ABUSEIPDB_WEIGHT

        risk_score = attack_contrib + confidence_contrib + vt_contrib + abuse_contrib
        risk_score = min(100.0, max(0.0, risk_score))

        risk_level = self.get_risk_level(risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "attack_score_used": round(effective_attack_score, 2),
            "cti_reputation_boost": (
                effective_attack_score > float(attack_score)
                and max(virustotal_score, abuse_effective) >= 20
            ),
            "reports_score": reports_score,
            "abuse_score_used": round(abuse_effective, 2),
            "is_whitelisted": bool(is_whitelisted),
            "weights": {
                "attack": ATTACK_WEIGHT,
                "confidence": CONFIDENCE_WEIGHT,
                "virustotal": VIRUSTOTAL_WEIGHT,
                "abuseipdb": ABUSEIPDB_WEIGHT,
            },
            "components": [
                {
                    "key": "attack",
                    "label": "Attack Severity",
                    "weight": ATTACK_WEIGHT,
                    "rawScore": round(effective_attack_score, 2),
                    "contribution": round(attack_contrib, 2),
                },
                {
                    "key": "confidence",
                    "label": "Model Confidence",
                    "weight": CONFIDENCE_WEIGHT,
                    "rawScore": round(model_confidence, 2),
                    "contribution": round(confidence_contrib, 2),
                },
                {
                    "key": "virustotal",
                    "label": "VirusTotal",
                    "weight": VIRUSTOTAL_WEIGHT,
                    "rawScore": round(virustotal_score, 2),
                    "contribution": round(vt_contrib, 2),
                },
                {
                    "key": "abuseipdb",
                    "label": "AbuseIPDB + Reports",
                    "weight": ABUSEIPDB_WEIGHT,
                    "rawScore": round(abuse_effective, 2),
                    "contribution": round(abuse_contrib, 2),
                },
            ],
            "formula": (
                "risk = 0.40*severity + 0.20*confidence + 0.20*VT + 0.20*abuse_effective; "
                "abuse_effective blends abuse confidence with log-scaled report volume; "
                "whitelist scales CTI; BENIGN + hot CTI uses reputation floor"
            ),
            "thresholds": {
                "SAFE": f"<{SAFE_THRESHOLD}",
                "LOW": f"<{LOW_THRESHOLD}",
                "MEDIUM": f"<{MEDIUM_THRESHOLD}",
                "HIGH": f"<{HIGH_THRESHOLD}",
                "CRITICAL": f">={HIGH_THRESHOLD}",
            },
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


def apply_temporal_risk(
    event_score: float,
    previous_dynamic: float | None = None,
    elapsed_seconds: float | None = None,
    repeat_attacks: int = 0,
    cti_unknown: bool = False,
) -> dict:
    """
    Dynamic risk = current evidence + decayed history + escalation - (implicit decay).

    Does not replace event_score; callers should keep both fields.
    """
    event_score = float(min(100.0, max(0.0, event_score)))
    half_life = 15 * 60.0
    decayed = 0.0
    decay = 0.0
    if previous_dynamic is not None:
        prior = float(previous_dynamic)
        if elapsed_seconds is None:
            decay = 0.5
        else:
            decay = 0.5 ** (max(0.0, float(elapsed_seconds)) / half_life)
        decayed = prior * decay
    escalation = min(15.0, max(0, int(repeat_attacks)) * 2.5)
    unknown_penalty = 8.0 if cti_unknown else 0.0
    blended = 0.75 * event_score + 0.25 * decayed
    dynamic = min(100.0, blended + escalation + unknown_penalty)
    return {
        "dynamic_risk_score": round(dynamic, 2),
        "decayed_prior": round(decayed, 2),
        "decay_factor": round(decay, 4),
        "escalation": round(escalation, 2),
        "unknown_cti_penalty": unknown_penalty,
        "half_life_seconds": half_life,
    }


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