from flask import Blueprint, jsonify

from backend.services.model_info_service import get_model_info

model_info_bp = Blueprint("model_info", __name__)


@model_info_bp.route("/model-info", methods=["GET"])
def model_info():
    """
    Model metadata
  ---
    tags:
      - Models
    responses:
      200:
        description: Random Forest and DQN metadata
    """
    return jsonify(get_model_info())
