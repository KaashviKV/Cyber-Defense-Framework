"""
Flask-Limiter configuration for API rate limiting.
"""

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.config.config import RATE_LIMIT_ANALYZE

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=[],
)


def register_rate_limiter(app: Flask) -> None:
    limiter.init_app(app)
    if app.config.get("TESTING"):
        limiter.enabled = False


def analyze_rate_limit() -> str:
    return RATE_LIMIT_ANALYZE
