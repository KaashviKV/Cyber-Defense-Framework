"""
Centralized Flask error handlers.
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from backend.middleware.request_context import current_request_id
from backend.utils.errors import APIError, error_response
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        if exc.status_code >= 500:
            logger.error(
                "API error",
                extra={
                    "request_id": current_request_id(),
                    "error_code": exc.code,
                    "detail": exc.message,
                },
            )
        return jsonify(error_response(
            code=exc.code,
            message=exc.message,
            request_id=current_request_id(),
            details=exc.details,
        )), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        code = exc.name.upper().replace(" ", "_") if exc.name else "HTTP_ERROR"
        return jsonify(error_response(
            code=code,
            message=exc.description or "HTTP error",
            request_id=current_request_id(),
        )), exc.code

    @app.errorhandler(404)
    def handle_not_found(exc):
        return jsonify(error_response(
            code="NOT_FOUND",
            message="The requested endpoint was not found.",
            request_id=current_request_id(),
        )), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(exc):
        return jsonify(error_response(
            code="METHOD_NOT_ALLOWED",
            message="HTTP method not allowed for this endpoint.",
            request_id=current_request_id(),
        )), 405

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        return jsonify(error_response(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please slow down and retry shortly.",
            request_id=current_request_id(),
        )), 429

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception(
            "Unhandled exception",
            extra={"request_id": current_request_id()},
        )
        return jsonify(error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            request_id=current_request_id(),
        )), 500
