"""
Model performance metrics service.
"""

from typing import Any

from ml.evaluate_model import get_model_performance_metrics


def get_model_performance_payload() -> dict[str, Any]:
    try:
        metrics = get_model_performance_metrics()
        return {
            "status": "success",
            **metrics,
        }
    except FileNotFoundError as exc:
        return {
            "status": "error",
            "code": "EVAL_DATA_MISSING",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "status": "error",
            "code": "MODEL_EVALUATION_FAILED",
            "message": str(exc),
        }
