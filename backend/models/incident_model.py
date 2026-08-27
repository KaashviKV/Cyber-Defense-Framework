"""Incident collection helpers. Failures must not break analyze."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.database.mongo import incidents_collection
from ml.mitre_mapping import KILL_CHAIN_ORDER


def _serialize(document: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(document)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    for key in ("first_seen", "last_seen"):
        value = data.get(key)
        if isinstance(value, datetime):
            data[key] = value.isoformat() + "Z"
    return data


def _next_incident_id() -> str:
    year = datetime.now(timezone.utc).year
    count = incidents_collection.count_documents({}) + 1
    return f"INC-{year}-{count:05d}"


def upsert_incident(analysis: dict[str, Any], analysis_id: Optional[str]) -> Optional[dict[str, Any]]:
    ip = analysis.get("ip_address")
    if not ip:
        return None
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=15)
    open_doc = incidents_collection.find_one(
        {
            "source_ips": ip,
            "disposition": "open",
            "last_seen": {"$gte": window_start},
        },
        sort=[("last_seen", -1)],
    )

    attack = (analysis.get("prediction") or {}).get("attack")
    mitre = analysis.get("mitre") or {}
    risk = analysis.get("risk") or {}
    action = (analysis.get("decision") or {}).get("action")
    event = {
        "analysis_id": analysis_id,
        "timestamp": now.isoformat(),
        "attack": attack,
        "risk_score": risk.get("risk_score"),
        "dynamic_risk_score": risk.get("dynamic_risk_score"),
        "action": action,
    }

    if open_doc is None:
        incident_id = _next_incident_id()
        document = {
            "incident_id": incident_id,
            "source_ips": [ip],
            "first_seen": now,
            "last_seen": now,
            "flow_count": 1,
            "analysis_ids": [analysis_id] if analysis_id else [],
            "attack_types": [attack] if attack else [],
            "mitre_techniques": [mitre] if mitre.get("technique_id") else [],
            "kill_chain": [mitre["kill_chain"]] if mitre.get("kill_chain") else [],
            "severity": risk.get("risk_level"),
            "current_risk": risk.get("dynamic_risk_score") or risk.get("risk_score"),
            "risk_history": [event],
            "actions": [action] if action else [],
            "current_response": action,
            "disposition": "open",
            "title": f"{'Suspicious' if attack and attack != 'BENIGN' else 'Observed'} host {ip}",
        }
        incidents_collection.insert_one(document)
        return _serialize(document)

    updates: dict[str, Any] = {
        "last_seen": now,
        "severity": risk.get("risk_level"),
        "current_risk": risk.get("dynamic_risk_score") or risk.get("risk_score"),
        "current_response": action,
    }
    incidents_collection.update_one(
        {"_id": open_doc["_id"]},
        {
            "$set": updates,
            "$inc": {"flow_count": 1},
            "$push": {
                "risk_history": {"$each": [event], "$slice": -40},
                "analysis_ids": {"$each": [analysis_id] if analysis_id else [], "$slice": -80},
                "actions": {"$each": [action] if action else [], "$slice": -40},
            },
            "$addToSet": {
                "attack_types": attack,
                **({"kill_chain": mitre["kill_chain"]} if mitre.get("kill_chain") else {}),
            },
        },
    )
    return get_incident_by_id(open_doc.get("incident_id"))


def list_incidents(limit: int = 50, skip: int = 0) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    skip = max(0, int(skip))
    cursor = incidents_collection.find().sort("last_seen", -1).skip(skip).limit(limit)
    rows = [_serialize(doc) for doc in cursor]
    for row in rows:
        stages = [s for s in (row.get("kill_chain") or []) if s]
        row["kill_chain_view"] = [
            {"stage": stage, "active": stage in stages} for stage in KILL_CHAIN_ORDER
        ]
    return rows


def get_incident_by_id(incident_id: str) -> Optional[dict[str, Any]]:
    document = incidents_collection.find_one({"incident_id": incident_id})
    if document is None:
        return None
    row = _serialize(document)
    stages = [s for s in (row.get("kill_chain") or []) if s]
    row["kill_chain_view"] = [
        {"stage": stage, "active": stage in stages} for stage in KILL_CHAIN_ORDER
    ]
    return row


def count_incidents() -> int:
    return incidents_collection.count_documents({})
