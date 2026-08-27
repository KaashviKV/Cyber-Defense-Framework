from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from backend.models.analysis_model import get_hitl_stats, get_metrics_summary
from backend.services.health_service import get_health_payload
from ml.calibration import ECE_PATH
from ml.drift import REFERENCE_PATH
from ml.model_registry import get_model_versions

model_health_bp = Blueprint("model_health", __name__)


@model_health_bp.route("/model-health", methods=["GET"])
def model_health():
    """
    Detector, RL, CTI, and drift health
    ---
    tags:
      - Models
    responses:
      200:
        description: Model health snapshot
    """
    health = get_health_payload()
    metrics = {}
    hitl = {}
    try:
        metrics = get_metrics_summary()
        hitl = get_hitl_stats()
    except Exception:
        metrics = {}
        hitl = {}

    return jsonify({
        "status": "success",
        "request_id": current_request_id(),
        "versions": get_model_versions(),
        "services": health.get("services"),
        "metrics": metrics,
        "hitl": hitl,
        "calibration_artifact": ECE_PATH.exists(),
        "drift_reference": REFERENCE_PATH.exists(),
        "notes": [
            "DQN production state remains 5-dimensional so existing weights keep working.",
            "Dynamic risk is stored alongside event risk and does not replace the fused formula.",
        ],
    })
