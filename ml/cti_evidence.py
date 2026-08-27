"""CTI provenance, freshness, and status (unknown ≠ clean)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def annotate_cti(payload: dict[str, Any], source: str) -> dict[str, Any]:
    data = dict(payload) if isinstance(payload, dict) else {"error": "invalid"}
    data.setdefault("source", source)
    if "queried_at" not in data:
        data["queried_at"] = utc_now_iso()
    data["age_seconds"] = age_seconds(data.get("queried_at"))
    data["freshness_weight"] = freshness_weight(data["age_seconds"], has_error="error" in data)
    return data


def age_seconds(queried_at: Optional[str]) -> Optional[float]:
    if not queried_at:
        return None
    try:
        stamp = datetime.fromisoformat(str(queried_at).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds())
    except (TypeError, ValueError):
        return None


def freshness_weight(age: Optional[float], has_error: bool = False) -> float:
    if has_error:
        return 0.0
    if age is None:
        return 1.0
    if age < 3600:
        return 1.0
    if age < 86400:
        return 0.70
    if age < 7 * 86400:
        return 0.40
    return 0.20


def classify_cti_status(
    vt_score: float,
    abuse_score: float,
    vt_error: bool,
    abuse_error: bool,
) -> str:
    if vt_error and abuse_error:
        return "unknown"
    heat = max(float(vt_score or 0), float(abuse_score or 0))
    if heat >= 60:
        return "confirmed_malicious"
    if heat >= 20:
        return "known_suspicious"
    if vt_error or abuse_error:
        return "unknown"
    return "clean"


def scale_for_freshness(score: float, weight: float) -> float:
    return round(float(score or 0) * float(weight), 2)
