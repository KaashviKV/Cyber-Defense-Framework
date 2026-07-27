from flask import Blueprint, request, jsonify
import numpy as np

from backend.pipeline import CyberDefensePipeline

analyze_bp = Blueprint("analyze", __name__)

pipeline = CyberDefensePipeline()


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data received."
            }), 400

        ip_address = data.get("ip_address")
        features = data.get("features")

        if ip_address is None:
            return jsonify({
                "status": "error",
                "message": "ip_address is required."
            }), 400

        if features is None:
            return jsonify({
                "status": "error",
                "message": "features are required."
            }), 400

        if len(features) != 78:
            return jsonify({
                "status": "error",
                "message": "Exactly 78 feature values are required."
            }), 400

        features = np.array(features)

        result = pipeline.analyze(
            features=features,
            ip_address=ip_address
        )

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500