from pathlib import Path
from typing import Literal

from backend.config.config import (
    ABUSEIPDB_API_KEY,
    DQN_MODEL_PATH,
    RF_MODEL_PATH,
    VIRUSTOTAL_API_KEY,
)
from backend.database.mongo import get_mongo_status


def _api_key_status(key: str) -> Literal["configured", "missing"]:
    if not key or key.startswith("your_") or key.endswith("_here"):
        return "missing"
    return "configured"


def _model_status(path: Path) -> Literal["loaded", "missing"]:
    return "loaded" if path.exists() else "missing"


def get_health_payload() -> dict:
    mongo_status = get_mongo_status()

    services = {
        "random_forest": _model_status(RF_MODEL_PATH),
        "dqn": _model_status(DQN_MODEL_PATH),
        "mongodb": mongo_status,
        "virustotal_api": _api_key_status(VIRUSTOTAL_API_KEY),
        "abuseipdb_api": _api_key_status(ABUSEIPDB_API_KEY),
    }

    return {
        "status": "ok",
        "service": "Intelligent Cyber Defense Framework",
        "services": services,
    }
