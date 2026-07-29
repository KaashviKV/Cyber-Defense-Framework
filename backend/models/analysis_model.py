"""
MongoDB helpers for analysis documents.
"""

import copy
from datetime import datetime, timezone
from typing import Any, Optional

from backend.config.config import API_VERSION, SCHEMA_VERSION
from backend.database.mongo import analysis_collection


def _serialize_document(document: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB types into JSON-safe values."""
    serialized = copy.deepcopy(document)

    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])

    timestamp = serialized.get("timestamp")
    if isinstance(timestamp, datetime):
        serialized["timestamp"] = timestamp.isoformat() + "Z"

    return serialized


def _cti_status(payload: Optional[dict[str, Any]]) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    return "error" if "error" in payload else "ok"


def build_api_status(report: dict[str, Any]) -> dict[str, str]:
    return {
        "virustotal": _cti_status(report.get("virustotal")),
        "abuseipdb": _cti_status(report.get("abuseipdb")),
        "mongodb": "pending",
    }


def enrich_analysis_document(report: dict[str, Any]) -> dict[str, Any]:
    """
    Add schema metadata before persistence without mutating the caller's dict.
    """
    document = copy.deepcopy(report)

    document.setdefault("schema_version", SCHEMA_VERSION)
    document.setdefault("api_version", API_VERSION)
    document.setdefault("api_status", build_api_status(document))

    if document.get("saved_to_mongodb") is not None:
        document["api_status"]["mongodb"] = (
            "saved" if document.get("saved_to_mongodb") else "not_saved"
        )
    else:
        document["api_status"]["mongodb"] = "pending"

    document["timestamp"] = datetime.now(timezone.utc)
    return document


def save_analysis(report: dict[str, Any]) -> str:
    """
    Persist an analysis report. Returns the inserted document id as a string.
    """
    document = enrich_analysis_document(report)
    document["api_status"]["mongodb"] = "saved"

    result = analysis_collection.insert_one(document)
    return str(result.inserted_id)


def get_analysis_history(limit: int = 50, skip: int = 0) -> list[dict[str, Any]]:
    """Return newest analysis documents first."""
    limit = max(1, min(int(limit), 200))
    skip = max(0, int(skip))

    cursor = (
        analysis_collection
        .find()
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    return [_serialize_document(doc) for doc in cursor]


def get_analysis_by_id(analysis_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single analysis by MongoDB ObjectId string."""
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        object_id = ObjectId(analysis_id)
    except InvalidId:
        return None

    document = analysis_collection.find_one({"_id": object_id})
    if document is None:
        return None

    return _serialize_document(document)


def count_analyses() -> int:
    return analysis_collection.count_documents({})


def get_metrics_summary() -> dict[str, Any]:
    """Aggregate metrics from stored analysis documents."""
    total = count_analyses()

    if total == 0:
        return {
            "total_analyses": 0,
            "average_risk": 0.0,
            "average_latency_ms": 0.0,
            "blocked_ips": 0,
            "alerts": 0,
            "isolations": 0,
        }

    pipeline = [
        {
            "$group": {
                "_id": None,
                "average_risk": {"$avg": "$risk.risk_score"},
                "average_latency_ms": {"$avg": "$performance.total_ms"},
            }
        }
    ]
    agg = list(analysis_collection.aggregate(pipeline))
    averages = agg[0] if agg else {}

    return {
        "total_analyses": total,
        "average_risk": round(float(averages.get("average_risk") or 0), 2),
        "average_latency_ms": round(float(averages.get("average_latency_ms") or 0), 2),
        "blocked_ips": analysis_collection.count_documents({"decision.action": "BLOCK_IP"}),
        "alerts": analysis_collection.count_documents({"decision.action": "ALERT_ADMIN"}),
        "isolations": analysis_collection.count_documents({"decision.action": "ISOLATE_HOST"}),
    }
