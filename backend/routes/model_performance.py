from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from backend.services.model_performance_service import get_model_performance_payload

model_performance_bp = Blueprint("model_performance", __name__)


@model_performance_bp.route("/model-performance", methods=["GET"])
def model_performance():
    """
    Random Forest evaluation metrics
    ---
    tags:
      - Models
    responses:
      200:
        description: Model accuracy, precision, recall, and F1 score
      503:
        description: Evaluation data or model unavailable
    """
    payload = get_model_performance_payload()
    payload["request_id"] = current_request_id()

    if payload.get("status") == "error":
        return jsonify(payload), 503

    return jsonify(payload)
