from flask import Blueprint, jsonify, request
import numpy as np

from backend.middleware.rate_limiter import analyze_rate_limit, limiter
from backend.middleware.request_context import get_or_create_request_id
from backend.services.container import ServiceContainer
from backend.utils.errors import APIError
from backend.utils.logging_config import get_logger
from backend.utils.validation import validate_features, validate_ip_address

logger = get_logger(__name__)

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
@limiter.limit(analyze_rate_limit)
def analyze():
    """
    Run full security analysis pipeline
    ---
    tags:
      - Analyze
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - ip_address
            - features
          properties:
            ip_address:
              type: string
              example: 8.8.8.8
            features:
              type: array
              items:
                type: number
              description: Exactly 78 numeric CICIDS2017 features
    responses:
      200:
        description: Analysis completed successfully
      400:
        description: Validation error
      429:
        description: Rate limit exceeded
      500:
        description: Internal server error
    """
    request_id = get_or_create_request_id()

    data = request.get_json(silent=True)
    if not data:
        raise APIError(
            message="No JSON data received.",
            code="INVALID_JSON",
            status_code=400,
        )

    ip_address = validate_ip_address(data.get("ip_address"))
    features = validate_features(data.get("features"))
    feature_array = np.array(features, dtype=float)

    logger.info(
        "Analyze request received",
        extra={"request_id": request_id, "ip": ip_address},
    )

    result = ServiceContainer.get_pipeline().analyze(
        features=feature_array,
        ip_address=ip_address,
        request_id=request_id,
    )

    return jsonify({
        "status": "success",
        "request_id": request_id,
        "analysis": result,
    })
