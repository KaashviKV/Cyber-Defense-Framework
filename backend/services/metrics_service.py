"""
Aggregate metrics from stored analyses.
"""

from typing import Any

from backend.database.mongo import get_mongo_status
from backend.models.analysis_model import get_metrics_summary
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_metrics_payload() -> dict[str, Any]:
    mongo_status = get_mongo_status()

    if mongo_status != "connected":
        return {
            "status": "success",
            "mongodb": mongo_status,
            "total_analyses": 0,
            "average_risk": 0.0,
            "average_latency_ms": 0.0,
            "blocked_ips": 0,
            "alerts": 0,
            "isolations": 0,
            "message": "Metrics unavailable while MongoDB is disconnected.",
        }

    try:
        summary = get_metrics_summary()
        summary["status"] = "success"
        summary["mongodb"] = mongo_status
        return summary
    except Exception as exc:
        logger.error("Failed to compute metrics", extra={"error": str(exc)})
        return {
            "status": "error",
            "mongodb": mongo_status,
            "code": "METRICS_ERROR",
            "message": str(exc),
        }
