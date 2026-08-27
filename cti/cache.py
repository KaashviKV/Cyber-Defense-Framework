"""
In-memory TTL cache for CTI lookups.
"""

import time
from threading import Lock
from typing import Any, Optional

from backend.config.config import CTI_CACHE_TTL_SECONDS

_lock = Lock()
_store: dict[str, tuple[float, dict[str, Any]]] = {}


def _cache_key(source: str, ip_address: str) -> str:
    return f"{source}:{ip_address.strip().lower()}"


def get_cached_cti(source: str, ip_address: str) -> Optional[dict[str, Any]]:
    key = _cache_key(source, ip_address)
    with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if time.time() > expires_at:
            _store.pop(key, None)
            return None
        cached = dict(payload)
        cached["cached"] = True
        return cached


def set_cached_cti(source: str, ip_address: str, payload: dict[str, Any]) -> None:
    key = _cache_key(source, ip_address)
    expires_at = time.time() + CTI_CACHE_TTL_SECONDS
    stored = dict(payload)
    stored.setdefault("queried_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with _lock:
        _store[key] = (expires_at, stored)


def clear_cti_cache() -> None:
    with _lock:
        _store.clear()
