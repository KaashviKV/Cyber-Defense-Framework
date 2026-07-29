"""
Request-scoped context helpers.
"""

import uuid
from typing import Optional

from flask import g, request


def get_or_create_request_id() -> str:
    """Return the current request ID, creating one if needed."""
    existing = getattr(g, "request_id", None)
    if existing:
        return existing

    header_id = request.headers.get("X-Request-ID", "").strip()
    request_id = header_id or str(uuid.uuid4())
    g.request_id = request_id
    return request_id


def current_request_id() -> Optional[str]:
    return getattr(g, "request_id", None)
