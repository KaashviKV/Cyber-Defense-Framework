"""In-process SSE fan-out for new analyses (no extra broker)."""

from __future__ import annotations

import json
from collections import deque
from threading import Lock
from typing import Any

_lock = Lock()
_latest: deque[dict[str, Any]] = deque(maxlen=50)


def publish_analysis(payload: dict[str, Any]) -> None:
    slim = {
        "analysis_id": payload.get("analysis_id"),
        "ip_address": payload.get("ip_address"),
        "attack": (payload.get("prediction") or {}).get("attack"),
        "risk_level": (payload.get("risk") or {}).get("risk_level"),
        "risk_score": (payload.get("risk") or {}).get("risk_score"),
        "action": (payload.get("decision") or {}).get("action"),
        "incident_id": (payload.get("incident") or {}).get("incident_id"),
    }
    with _lock:
        _latest.appendleft(slim)


def latest(n: int = 10) -> list[dict[str, Any]]:
    with _lock:
        return list(_latest)[:n]


def snapshot_json() -> str:
    return json.dumps({"events": latest(15)})
