"""
Tests for CTI-aware RL without breaking legacy behavior.
"""

from pathlib import Path

import torch

from ml.rl.predict_action import RLDecisionMaker
from ml.rl.state_encoder import (
    STATE_SIZE_V1,
    STATE_SIZE_V2,
    encode_state,
    infer_state_size_from_checkpoint,
)
from ml.response_engine.decision_engine import DecisionEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DQN_PATH = PROJECT_ROOT / "ml" / "saved_models" / "dqn_model.pth"
LEGACY_PATH = PROJECT_ROOT / "ml" / "saved_models" / "dqn_model_v1_legacy.pth"


def test_encode_state_sizes():
    v1 = encode_state(50, 60, state_size=STATE_SIZE_V1)
    v2 = encode_state(50, 60, confidence=80, virustotal_score=10, abuseipdb_score=20, state_size=STATE_SIZE_V2)
    assert len(v1) == 2
    assert len(v2) == 5
    assert all(0.0 <= x <= 1.0 for x in v1 + v2)


def test_infer_state_size_from_current_checkpoint():
    state_dict = torch.load(DQN_PATH, map_location="cpu")
    size = infer_state_size_from_checkpoint(state_dict)
    assert size in (STATE_SIZE_V1, STATE_SIZE_V2)


def test_rl_decision_maker_loads_and_predicts():
    rl = RLDecisionMaker()
    action = rl.predict(10, 15, confidence=80, virustotal_score=2, abuseipdb_score=3)
    assert action in {"NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"}


def test_decision_engine_legacy_signature_still_works():
    engine = DecisionEngine()
    result = engine.decide("8.8.8.8", 10, 15)
    assert result["status"] == "SUCCESS"
    assert result["action"] in {"NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"}
    assert "rl_model_version" in result


def test_decision_engine_cti_signature():
    engine = DecisionEngine()
    result = engine.decide(
        "1.2.3.4",
        95,
        90,
        confidence=96,
        virustotal_score=80,
        abuseipdb_score=85,
    )
    assert result["status"] == "SUCCESS"
    assert result["rl_state_size"] in (2, 5)


def test_legacy_checkpoint_still_loadable_if_present():
    if not LEGACY_PATH.exists():
        return
    rl = RLDecisionMaker(str(LEGACY_PATH))
    assert rl.state_size == STATE_SIZE_V1
    assert rl.predict(10, 15) in {"NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"}
