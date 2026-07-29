"""
Structured logging configuration for the backend.
"""

import logging
from logging.handlers import RotatingFileHandler

from backend.config.config import BACKEND_LOG_FILE, ERROR_LOG_FILE, LOG_DIR, LOG_LEVEL


def setup_logging() -> None:
    """Configure application-wide logging once at startup."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if getattr(root, "_icdf_configured", False):
        return

    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    backend_handler = RotatingFileHandler(
        BACKEND_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    backend_handler.setFormatter(formatter)
    root.addHandler(backend_handler)

    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    root._icdf_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
