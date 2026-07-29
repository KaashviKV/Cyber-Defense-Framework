from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from backend.services.feature_importance_service import get_feature_importance

feature_importance_bp = Blueprint("feature_importance", __name__)


@feature_importance_bp.route("/feature-importance", methods=["GET"])
def feature_importance():
    """
    Top Random Forest feature importances
    ---
    tags:
      - Models
    responses:
      200:
        description: Global feature importance scores
    """
    payload = get_feature_importance()
    payload["request_id"] = current_request_id()
    status = 200 if payload.get("status") == "success" else 503
    return jsonify(payload), status
