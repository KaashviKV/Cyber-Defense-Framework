"""
Model metadata for API consumers and dashboard.
"""

from typing import Any

from backend.config.config import (
    ATTACK_CLASS_COUNT,
    DATASET_NAME,
    DQN_MODEL_PATH,
    FEATURE_COUNT,
    RF_MODEL_PATH,
    RL_ACTION_COUNT,
)
from backend.services.health_service import get_health_payload


def get_model_info() -> dict[str, Any]:
    health = get_health_payload()

    return {
        "status": "success",
        "random_forest": health["services"]["random_forest"],
        "algorithm": "Random Forest",
        "dataset": DATASET_NAME,
        "features": FEATURE_COUNT,
        "attack_classes": ATTACK_CLASS_COUNT,
        "rl_algorithm": "Deep Q Network",
        "dqn": health["services"]["dqn"],
        "actions": RL_ACTION_COUNT,
        "action_labels": [
            "NO_ACTION",
            "ALERT_ADMIN",
            "BLOCK_IP",
            "ISOLATE_HOST",
        ],
        "rl_state": _rl_state_info(),
        "model_paths": {
            "random_forest": str(RF_MODEL_PATH),
            "dqn": str(DQN_MODEL_PATH),
        },
    }


def _rl_state_info() -> dict[str, Any]:
    try:
        from ml.rl.predict_action import RLDecisionMaker
        from ml.rl.state_encoder import STATE_FEATURE_NAMES_V2

        rl = RLDecisionMaker()
        features = (
            STATE_FEATURE_NAMES_V2
            if rl.state_size == 5
            else ["severity", "risk_score"]
        )
        return {
            "model_version": rl.model_version,
            "state_size": rl.state_size,
            "features": features,
        }
    except Exception as exc:
        return {
            "model_version": "unavailable",
            "state_size": None,
            "features": [],
            "error": str(exc),
        }
