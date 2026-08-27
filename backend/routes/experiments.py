from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from backend.services.experiments_service import get_experiments_payload

experiments_bp = Blueprint("experiments", __name__)


@experiments_bp.route("/experiments", methods=["GET"])
def experiments():
    """
    Research experiment artifacts
    ---
    tags:
      - Experiments
    responses:
      200:
        description: Saved experiment JSON summaries for the dashboard
    """
    payload = get_experiments_payload()
    payload["request_id"] = current_request_id()
    return jsonify(payload)
