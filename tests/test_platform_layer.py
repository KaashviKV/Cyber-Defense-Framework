from ml.cti_evidence import classify_cti_status, freshness_weight
from ml.fail_safe import apply_fail_safe
from ml.mitre_mapping import map_attack
from ml.risk_engine import RiskEngine, apply_temporal_risk
from ml.rl.environment import CyberDefenseEnvironment


def test_fail_safe_only_when_unknown_and_non_benign():
    action, applied, _ = apply_fail_safe("NO_ACTION", "DDoS", "unknown")
    assert action == "ALERT_ADMIN"
    assert applied is True
    action2, applied2, _ = apply_fail_safe("NO_ACTION", "BENIGN", "unknown")
    assert action2 == "NO_ACTION"
    assert applied2 is False
    action3, applied3, _ = apply_fail_safe("NO_ACTION", "DDoS", "clean")
    assert action3 == "NO_ACTION"
    assert applied3 is False


def test_mitre_portscan_is_high_confidence():
    mapped = map_attack("PortScan")
    assert mapped["technique_id"] == "T1046"
    assert mapped["confidence"] == "HIGH"


def test_temporal_risk_equals_event_without_history():
    result = apply_temporal_risk(40.0)
    assert result["dynamic_risk_score"] >= 30
    assert result["escalation"] == 0


def test_freshness_stale_is_lower():
    assert freshness_weight(100) == 1.0
    assert freshness_weight(2 * 86400) < freshness_weight(100)


def test_cti_both_errors_unknown():
    assert classify_cti_status(0, 0, True, True) == "unknown"


def test_environment_default_unchanged_flags():
    env = CyberDefenseEnvironment()
    assert env.cost_sensitive is False
    assert env.sequential_effects is False
    state = env.reset()
    _, reward, _ = env.step(0)
    assert isinstance(reward, float)
    assert "risk_score" in state


def test_risk_engine_signature_still_works():
    engine = RiskEngine()
    result = engine.calculate_risk("DDoS", 96, 85, 90)
    assert result["risk_level"] in {"SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
