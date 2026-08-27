"""Lightweight model registry stamps (does not move existing .pkl/.pth files)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config.config import DQN_MODEL_PATH, RF_MODEL_PATH, SAVED_MODELS_DIR

MANIFEST_PATH = SAVED_MODELS_DIR / "registry" / "manifest.json"


def _ensure_manifest() -> dict[str, Any]:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError:
            pass
    payload = {
        "detector_version": "rf-1.0",
        "policy_version": "dqn-2.0",
        "risk_engine_version": "risk-1.4",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "random_forest": str(RF_MODEL_PATH),
            "dqn": str(DQN_MODEL_PATH),
        },
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return payload


def get_model_versions() -> dict[str, str]:
    data = _ensure_manifest()
    return {
        "detector_version": str(data.get("detector_version") or "rf-1.0"),
        "policy_version": str(data.get("policy_version") or "dqn-2.0"),
        "risk_engine_version": str(data.get("risk_engine_version") or "risk-1.4"),
    }
