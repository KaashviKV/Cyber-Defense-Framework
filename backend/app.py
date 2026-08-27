from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from backend.middleware.error_handlers import register_error_handlers
from backend.middleware.rate_limiter import register_rate_limiter
from backend.middleware.request_context import get_or_create_request_id, current_request_id
from backend.middleware.security import register_security_headers
from backend.routes.analyze import analyze_bp
from backend.routes.experiments import experiments_bp
from backend.routes.feature_importance import feature_importance_bp
from backend.routes.history import history_bp
from backend.routes.metrics import metrics_bp
from backend.routes.model_info import model_info_bp
from backend.routes.model_performance import model_performance_bp
from backend.routes.simulation import simulation_bp
from backend.routes.incidents import incidents_bp
from backend.routes.model_health import model_health_bp
from backend.routes.stream import stream_bp
from backend.services.container import ServiceContainer
from backend.services.health_service import get_health_payload
from backend.services.startup_service import log_startup_report
from backend.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
}

SWAGGER_TEMPLATE = {
    "info": {
        "title": "Intelligent Cyber Defense Framework API",
        "description": "AI-powered adaptive network security API",
        "version": "1.0.0",
    },
    "tags": [
        {"name": "Analyze", "description": "Run the full ML + CTI + RL pipeline"},
        {"name": "History", "description": "Stored analysis history"},
        {"name": "Health", "description": "Service health and dependency status"},
        {"name": "Models", "description": "Model metadata and evaluation"},
        {"name": "Metrics", "description": "Aggregated performance metrics"},
        {"name": "Experiments", "description": "Saved research experiment artifacts"},
        {"name": "Incidents", "description": "Temporal SOC incidents"},
        {"name": "Stream", "description": "Live analysis events"},
    ],
}


def create_app(testing: bool = False) -> Flask:
    setup_logging()
    log_startup_report()
    ServiceContainer.init(eager=not testing)

    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    CORS(app)
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    register_security_headers(app)
    register_error_handlers(app)
    register_rate_limiter(app)

    @app.before_request
    def attach_request_id():
        get_or_create_request_id()

    app.register_blueprint(analyze_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(model_info_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(model_performance_bp)
    app.register_blueprint(feature_importance_bp)
    app.register_blueprint(experiments_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(model_health_bp)
    app.register_blueprint(stream_bp)

    app.register_blueprint(analyze_bp, url_prefix="/api/v1", name="analyze_v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1", name="history_v1")
    app.register_blueprint(model_info_bp, url_prefix="/api/v1", name="model_info_v1")
    app.register_blueprint(metrics_bp, url_prefix="/api/v1", name="metrics_v1")
    app.register_blueprint(model_performance_bp, url_prefix="/api/v1", name="model_performance_v1")
    app.register_blueprint(feature_importance_bp, url_prefix="/api/v1", name="feature_importance_v1")
    app.register_blueprint(experiments_bp, url_prefix="/api/v1", name="experiments_v1")
    app.register_blueprint(simulation_bp, url_prefix="/api/v1", name="simulation_v1")
    app.register_blueprint(incidents_bp, url_prefix="/api/v1", name="incidents_v1")
    app.register_blueprint(model_health_bp, url_prefix="/api/v1", name="model_health_v1")
    app.register_blueprint(stream_bp, url_prefix="/api/v1", name="stream_v1")

    @app.route("/health", methods=["GET"])
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        """
        API health check
        ---
        tags:
          - Health
        responses:
          200:
            description: Service and dependency status
        """
        payload = get_health_payload()
        payload["request_id"] = current_request_id()
        return jsonify(payload)

    logger.info("Flask application created")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
