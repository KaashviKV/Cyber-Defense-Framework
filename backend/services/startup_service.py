"""
Startup environment validation.
"""

from typing import Any

from backend.config.config import (
    ABUSEIPDB_API_KEY,
    DQN_MODEL_PATH,
    RF_MODEL_PATH,
    VIRUSTOTAL_API_KEY,
)
from backend.database.mongo import get_mongo_status
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def _api_key_ok(key: str) -> bool:
    return bool(key) and not key.startswith("your_") and not key.endswith("_here")


def validate_environment() -> dict[str, Any]:
    checks = {
        "random_forest_model": {
            "ok": RF_MODEL_PATH.exists(),
            "detail": str(RF_MODEL_PATH),
        },
        "dqn_model": {
            "ok": DQN_MODEL_PATH.exists(),
            "detail": str(DQN_MODEL_PATH),
        },
        "mongodb": {
            "ok": get_mongo_status() == "connected",
            "detail": get_mongo_status(),
        },
        "virustotal_api": {
            "ok": _api_key_ok(VIRUSTOTAL_API_KEY),
            "detail": "configured" if _api_key_ok(VIRUSTOTAL_API_KEY) else "missing",
        },
        "abuseipdb_api": {
            "ok": _api_key_ok(ABUSEIPDB_API_KEY),
            "detail": "configured" if _api_key_ok(ABUSEIPDB_API_KEY) else "missing",
        },
    }

    required = {"random_forest_model", "dqn_model"}
    ready = all(checks[name]["ok"] for name in required)

    return {
        "ready": ready,
        "checks": checks,
    }


def log_startup_report() -> None:
    report = validate_environment()
    logger.info("=== Startup Environment Validation ===")

    labels = {
        "random_forest_model": "Random Forest model",
        "dqn_model": "DQN model",
        "mongodb": "MongoDB",
        "virustotal_api": "VirusTotal API",
        "abuseipdb_api": "AbuseIPDB API",
    }

    for key, label in labels.items():
        ok = report["checks"][key]["ok"]
        symbol = "[OK]" if ok else "[MISSING]"
        detail = report["checks"][key]["detail"]
        logger.info("%s %s - %s", symbol, label, detail)

    if report["ready"]:
        logger.info("Core models loaded. API server ready.")
    else:
        logger.warning("Core models missing. Analysis may fail until models are available.")
