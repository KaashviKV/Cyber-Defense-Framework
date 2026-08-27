"""Rolling IP/session windows over stored analyses (no live packet capture)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


WINDOWS_SECONDS = (30, 5 * 60, 15 * 60)


def _ts(doc: dict[str, Any]) -> datetime | None:
    value = doc.get("timestamp")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def summarize_session(ip_address: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    windows: dict[str, dict[str, Any]] = {}
    for seconds in WINDOWS_SECONDS:
        label = f"last_{seconds}s"
        subset = []
        for doc in documents:
            stamp = _ts(doc)
            if stamp is None:
                continue
            if (now - stamp).total_seconds() <= seconds:
                subset.append(doc)
        attacks = [d.get("prediction", {}).get("attack") for d in subset if d.get("prediction")]
        risks = [float(d.get("risk", {}).get("risk_score") or 0) for d in subset]
        confs = [float(d.get("prediction", {}).get("confidence") or 0) for d in subset]
        windows[label] = {
            "flow_count": len(subset),
            "unique_attack_types": len({a for a in attacks if a}),
            "attack_distribution": dict(Counter(a for a in attacks if a)),
            "mean_confidence": round(sum(confs) / len(confs), 2) if confs else 0.0,
            "max_confidence": round(max(confs), 2) if confs else 0.0,
            "mean_risk": round(sum(risks) / len(risks), 2) if risks else 0.0,
            "max_risk": round(max(risks), 2) if risks else 0.0,
            "risk_trajectory": [round(r, 2) for r in risks[:12]],
        }

    non_benign = sum(
        1
        for d in documents
        if (d.get("prediction") or {}).get("attack") not in (None, "BENIGN")
    )
    previous = documents[0] if documents else None
    prev_risk = None
    prev_action = None
    elapsed = None
    if previous:
        prev_risk = (previous.get("risk") or {}).get("dynamic_risk_score")
        if prev_risk is None:
            prev_risk = (previous.get("risk") or {}).get("risk_score")
        prev_action = (previous.get("decision") or {}).get("action")
        stamp = _ts(previous)
        if stamp:
            elapsed = (now - stamp).total_seconds()

    return {
        "ip_address": ip_address,
        "lookback_documents": len(documents),
        "windows": windows,
        "repeat_attack_count": non_benign,
        "previous_dynamic_risk": prev_risk,
        "previous_action": prev_action,
        "seconds_since_previous": elapsed,
    }
