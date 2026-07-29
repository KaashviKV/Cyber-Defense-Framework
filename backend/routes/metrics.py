from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from backend.services.metrics_service import get_metrics_payload

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def metrics():
    """
    Performance and threat metrics
    ---
    tags:
      - Metrics
    responses:
      200:
        description: Aggregated analysis metrics
    """
    payload = get_metrics_payload()
    payload["request_id"] = current_request_id()
    return jsonify(payload)
