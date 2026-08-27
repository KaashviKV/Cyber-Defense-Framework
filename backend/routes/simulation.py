from flask import Blueprint, jsonify

from backend.middleware.request_context import current_request_id
from ml.response_engine.simulation_state import get_simulation_summary

simulation_bp = Blueprint("simulation", __name__)


@simulation_bp.route("/simulation", methods=["GET"])
def simulation():
    """
    Simulated SOC response state
    ---
    tags:
      - Response
    responses:
      200:
        description: Simulated blocklist, isolation, and alert logs
    """
    payload = get_simulation_summary()
    payload["request_id"] = current_request_id()
    return jsonify(payload)
