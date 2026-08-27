from ml.risk_engine import RiskEngine, normalize_report_score
from ml.rl.baselines import ml_only_action, rule_based_action
from ml.rl.explain_action import explain_rl_decision
from ml.response_engine.simulation_state import get_simulation_summary, record_event


def test_report_score_zero_when_missing():
    assert normalize_report_score(0) == 0.0
    assert normalize_report_score(None) == 0.0


def test_risk_engine_reports_do_not_change_zero_report_formula():
    engine = RiskEngine()
    a = engine.calculate_risk("DDoS", 96, 85, 90)
    b = engine.calculate_risk("DDoS", 96, 85, 90, total_reports=0)
    assert a["risk_score"] == b["risk_score"]
    assert "components" in a
    assert a["weights"]["attack"] == 0.4


def test_whitelist_reduces_cti_driven_risk():
    engine = RiskEngine()
    hot = engine.calculate_risk("BENIGN", 80, 10, 90, total_reports=100)
    listed = engine.calculate_risk(
        "BENIGN", 80, 10, 90, total_reports=100, is_whitelisted=True
    )
    assert listed["risk_score"] < hot["risk_score"]


def test_rule_based_benign_is_no_action():
    assert rule_based_action({
        "attack": "BENIGN",
        "risk_score": 10,
        "virustotal_score": 1,
        "abuseipdb_score": 0,
    }) == "NO_ACTION"


def test_ml_only_ignores_hot_cti_on_benign():
    state = {
        "attack": "BENIGN",
        "severity": 0,
        "risk_score": 70,
        "virustotal_score": 80,
        "abuseipdb_score": 90,
    }
    assert ml_only_action(state) == "NO_ACTION"
    assert rule_based_action(state) in {"BLOCK_IP", "ISOLATE_HOST", "ALERT_ADMIN"}


def test_rl_explanation_is_context_not_oracle():
    payload = explain_rl_decision(
        action="BLOCK_IP",
        attack="DDoS",
        severity=95,
        confidence=90,
        risk_score=82,
        risk_level="CRITICAL",
        virustotal_score=70,
        abuseipdb_score=80,
        q_values=[0.1, 0.2, 1.5, 0.4],
    )
    assert "causal" in payload["caveat"].lower() or "not" in payload["caveat"].lower()
    assert payload["q_ranking"][0]["action"] == "BLOCK_IP"


def test_simulation_records_blocklist(tmp_path, monkeypatch):
    import ml.response_engine.simulation_state as sim

    monkeypatch.setattr(sim, "STATE_PATH", str(tmp_path / "state.json"))
    record_event("BLOCK_IP", "1.2.3.4")
    summary = get_simulation_summary()
    assert summary["counts"]["blocklist"] == 1
    assert summary["blocklist"][0]["ip"] == "1.2.3.4"
