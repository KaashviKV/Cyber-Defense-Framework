"""
API error types and standardized error payloads.
"""

from typing import Any, Optional


class APIError(Exception):
    """Raised for predictable client-facing API errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


def error_response(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if request_id:
        payload["request_id"] = request_id
    if details:
        payload["details"] = details
    return payload
