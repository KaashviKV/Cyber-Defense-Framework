"""
====================================================
Intelligent Cyber Defense Framework
Main Integration Pipeline
====================================================
"""

import os
import sys
import time
from typing import Any, Optional

import numpy as np

from backend.config.config import API_VERSION
from backend.models.analysis_model import build_api_status, save_analysis
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PROJECT_ROOT)

from ml.predict import predict_attack
from cti.virustotal import check_virustotal
from cti.abuseipdb import check_abuseip
from ml.risk_engine import RiskEngine, normalize_virustotal_score
from ml.response_engine.decision_engine import DecisionEngine


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


class CyberDefensePipeline:

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()
        self.decision_engine = DecisionEngine()

    def analyze(
        self,
        features: np.ndarray,
        ip_address: str,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        total_start = time.perf_counter()
        performance: dict[str, int] = {}

        log_extra = {"ip": ip_address, "request_id": request_id}
        logger.info("Analysis started", extra=log_extra)

        step_start = time.perf_counter()
        prediction = predict_attack(features)
        performance["prediction_ms"] = _elapsed_ms(step_start)
        logger.info(
            "Prediction complete",
            extra={
                **log_extra,
                "attack": prediction.get("attack"),
                "confidence": prediction.get("confidence"),
                "duration_ms": performance["prediction_ms"],
            },
        )

        attack = prediction["attack"]
        severity = prediction["severity"]
        confidence = prediction["confidence"]

        step_start = time.perf_counter()
        vt = check_virustotal(ip_address)
        performance["virustotal_ms"] = _elapsed_ms(step_start)
        if "error" in vt:
            logger.warning(
                "VirusTotal unavailable",
                extra={**log_extra, "error": vt.get("error"), "duration_ms": performance["virustotal_ms"]},
            )
        else:
            logger.info("VirusTotal lookup complete", extra={**log_extra, "duration_ms": performance["virustotal_ms"]})

        vt_score = normalize_virustotal_score(vt)

        step_start = time.perf_counter()
        abuse = check_abuseip(ip_address)
        performance["abuseipdb_ms"] = _elapsed_ms(step_start)
        if "error" in abuse:
            logger.warning(
                "AbuseIPDB unavailable",
                extra={**log_extra, "error": abuse.get("error"), "duration_ms": performance["abuseipdb_ms"]},
            )
        else:
            logger.info("AbuseIPDB lookup complete", extra={**log_extra, "duration_ms": performance["abuseipdb_ms"]})

        abuse_score = abuse.get("abuse_confidence", 0) if "error" not in abuse else 0

        step_start = time.perf_counter()
        risk = self.risk_engine.calculate_risk(
            attack_name=attack,
            model_confidence=confidence,
            virustotal_score=vt_score,
            abuse_score=abuse_score,
        )
        risk["virustotal_score"] = vt_score
        risk["abuseipdb_score"] = abuse_score
        performance["risk_engine_ms"] = _elapsed_ms(step_start)
        logger.info(
            "Risk calculated",
            extra={
                **log_extra,
                "risk_level": risk.get("risk_level"),
                "risk_score": risk.get("risk_score"),
                "duration_ms": performance["risk_engine_ms"],
            },
        )

        step_start = time.perf_counter()
        decision = self.decision_engine.decide(
            ip_address=ip_address,
            attack_severity=severity,
            risk_score=risk["risk_score"],
        )
        performance["dqn_ms"] = _elapsed_ms(step_start)
        logger.info(
            "Decision complete",
            extra={
                **log_extra,
                "action": decision.get("action"),
                "duration_ms": performance["dqn_ms"],
            },
        )

        performance["total_ms"] = _elapsed_ms(total_start)

        result: dict[str, Any] = {
            "ip_address": ip_address,
            "request_id": request_id,
            "api_version": API_VERSION,
            "prediction": prediction,
            "virustotal": vt,
            "abuseipdb": abuse,
            "risk": risk,
            "decision": decision,
            "performance": performance,
            "api_status": build_api_status({
                "virustotal": vt,
                "abuseipdb": abuse,
            }),
        }

        try:
            analysis_id = save_analysis(result)
            result["analysis_id"] = analysis_id
            result["saved_to_mongodb"] = True
            result["api_status"]["mongodb"] = "saved"
            logger.info(
                "Analysis saved to MongoDB",
                extra={**log_extra, "analysis_id": analysis_id},
            )
        except Exception as exc:
            result["analysis_id"] = None
            result["saved_to_mongodb"] = False
            result["mongodb_error"] = str(exc)
            result["api_status"]["mongodb"] = "error"
            logger.error(
                "MongoDB save failed",
                extra={**log_extra, "error": str(exc)},
            )

        logger.info(
            "Analysis completed",
            extra={**log_extra, "total_ms": performance["total_ms"]},
        )

        return result


if __name__ == "__main__":
    pipeline = CyberDefensePipeline()
    dummy_features = np.random.rand(78)
    ip = input("Enter IP Address : ")
    report = pipeline.analyze(features=dummy_features, ip_address=ip, request_id="cli-test")
    from pprint import pprint

    pprint(report)
