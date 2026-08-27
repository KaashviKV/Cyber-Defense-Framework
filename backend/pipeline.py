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
from backend.models.analysis_model import build_api_status, get_recent_analyses_for_ip, save_analysis
from backend.models.incident_model import upsert_incident
from backend.services.event_bus import publish_analysis
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PROJECT_ROOT)

from ml.predict import explain_prediction, predict_attack
from cti.virustotal import check_virustotal
from cti.abuseipdb import check_abuseip
from ml.risk_engine import RiskEngine, apply_temporal_risk, normalize_virustotal_score
from ml.response_engine.decision_engine import DecisionEngine
from ml.cti_evidence import annotate_cti, classify_cti_status, scale_for_freshness
from ml.mitre_mapping import map_attack
from ml.session_aggregator import summarize_session
from ml.drift import evaluate_vector
from ml.model_registry import get_model_versions

logger = get_logger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PROJECT_ROOT)

from ml.predict import explain_prediction, predict_attack
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
        vt = annotate_cti(check_virustotal(ip_address), "VirusTotal")
        performance["virustotal_ms"] = _elapsed_ms(step_start)
        if "error" in vt:
            logger.warning(
                "VirusTotal unavailable",
                extra={**log_extra, "error": vt.get("error"), "duration_ms": performance["virustotal_ms"]},
            )
        else:
            logger.info("VirusTotal lookup complete", extra={**log_extra, "duration_ms": performance["virustotal_ms"]})

        vt_raw = normalize_virustotal_score(vt)

        step_start = time.perf_counter()
        abuse = annotate_cti(check_abuseip(ip_address), "AbuseIPDB")
        performance["abuseipdb_ms"] = _elapsed_ms(step_start)
        if "error" in abuse:
            logger.warning(
                "AbuseIPDB unavailable",
                extra={**log_extra, "error": abuse.get("error"), "duration_ms": performance["abuseipdb_ms"]},
            )
        else:
            logger.info("AbuseIPDB lookup complete", extra={**log_extra, "duration_ms": performance["abuseipdb_ms"]})

        abuse_raw = abuse.get("abuse_confidence", 0) if "error" not in abuse else 0
        total_reports = abuse.get("total_reports", 0) if "error" not in abuse else 0
        is_whitelisted = bool(abuse.get("is_whitelisted")) if "error" not in abuse else False
        cti_status = classify_cti_status(
            vt_raw,
            abuse_raw,
            vt_error="error" in vt,
            abuse_error="error" in abuse,
        )
        vt_score = scale_for_freshness(vt_raw, vt.get("freshness_weight", 1.0) if "error" not in vt else 0.0)
        abuse_score = scale_for_freshness(
            abuse_raw, abuse.get("freshness_weight", 1.0) if "error" not in abuse else 0.0
        )

        session = {"windows": {}, "repeat_attack_count": 0}
        try:
            recent = get_recent_analyses_for_ip(ip_address, minutes=15)
            session = summarize_session(ip_address, recent)
        except Exception as exc:
            logger.warning("Session aggregation skipped", extra={**log_extra, "error": str(exc)})

        step_start = time.perf_counter()
        xai = explain_prediction(features, top_n=5)
        performance["explainability_ms"] = _elapsed_ms(step_start)

        step_start = time.perf_counter()
        risk = self.risk_engine.calculate_risk(
            attack_name=attack,
            model_confidence=confidence,
            virustotal_score=vt_score,
            abuse_score=abuse_score,
            total_reports=total_reports,
            is_whitelisted=is_whitelisted,
        )
        temporal = apply_temporal_risk(
            risk["risk_score"],
            previous_dynamic=session.get("previous_dynamic_risk"),
            elapsed_seconds=session.get("seconds_since_previous"),
            repeat_attacks=session.get("repeat_attack_count") or 0,
            cti_unknown=cti_status == "unknown",
        )
        risk.update(temporal)
        risk["event_risk_score"] = risk["risk_score"]
        risk["virustotal_score"] = vt_raw
        risk["abuseipdb_score"] = abuse_raw
        risk["cti_status"] = cti_status
        risk["dynamic_risk_level"] = self.risk_engine.get_risk_level(temporal["dynamic_risk_score"])
        performance["risk_engine_ms"] = _elapsed_ms(step_start)

        previous_action = session.get("previous_action")
        response_change = None
        if previous_action and previous_action != "pending":
            # filled after decision
            pass

        mitre = map_attack(attack)
        drift = evaluate_vector(features)
        versions = get_model_versions()

        step_start = time.perf_counter()
        decision = self.decision_engine.decide(
            ip_address=ip_address,
            attack_severity=severity,
            risk_score=risk["risk_score"],
            confidence=confidence,
            virustotal_score=vt_score,
            abuseipdb_score=abuse_score,
            attack_name=attack,
            risk_level=risk.get("risk_level", ""),
            cti_status=cti_status,
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

        if previous_action and previous_action != decision.get("action"):
            response_change = {
                "previous_action": previous_action,
                "new_action": decision.get("action"),
                "previous_dynamic_risk": session.get("previous_dynamic_risk"),
                "new_dynamic_risk": risk.get("dynamic_risk_score"),
                "reason": (
                    "Response changed relative to the last event on this IP. "
                    "Compare dynamic risk, CTI status, and fail-safe flags rather than treating DQN as causal."
                ),
            }

        performance["total_ms"] = _elapsed_ms(total_start)

        audit_trail = [
            {"step": "ml", "detail": f"{attack} (confidence {confidence})"},
            {"step": "cti", "detail": f"status={cti_status} vt={vt_raw} abuse={abuse_raw}"},
            {"step": "risk", "detail": f"event={risk['risk_score']} dynamic={risk.get('dynamic_risk_score')}"},
            {"step": "dqn", "detail": decision.get("policy_action") or decision.get("action")},
            {"step": "fail_safe", "detail": decision.get("fail_safe_reason") or "not applied"},
            {"step": "response", "detail": decision.get("action")},
        ]

        result: dict[str, Any] = {
            "ip_address": ip_address,
            "request_id": request_id,
            "api_version": API_VERSION,
            "prediction": prediction,
            "mitre": mitre,
            "virustotal": vt,
            "abuseipdb": abuse,
            "risk": risk,
            "session": session,
            "decision": decision,
            "explanation": xai,
            "drift": drift,
            "model_versions": versions,
            "response_change": response_change,
            "audit_trail": audit_trail,
            "feedback_loop": {
                "status": "pending_analyst_review",
                "hint": "Submit analyst feedback on this analysis to support later RL fine-tuning.",
            },
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
            try:
                incident = upsert_incident(result, analysis_id)
                result["incident"] = {
                    "incident_id": (incident or {}).get("incident_id"),
                    "flow_count": (incident or {}).get("flow_count"),
                    "current_response": (incident or {}).get("current_response"),
                    "kill_chain_view": (incident or {}).get("kill_chain_view"),
                }
            except Exception as exc:
                logger.warning("Incident upsert skipped", extra={**log_extra, "error": str(exc)})
                result["incident"] = None
            try:
                publish_analysis(result)
            except Exception:
                pass
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
