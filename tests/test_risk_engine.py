from ml.risk_engine import RiskEngine, normalize_virustotal_score


def test_normalize_virustotal_score_zero_when_error():
    assert normalize_virustotal_score({"error": 401}) == 0.0


def test_normalize_virustotal_score_malicious_only():
    score = normalize_virustotal_score({
        "malicious": 50,
        "suspicious": 0,
        "harmless": 50,
        "undetected": 0,
    })
    assert score == 50.0


def test_risk_engine_benign_with_malicious_ip_gets_high_risk():
    engine = RiskEngine()
    result = engine.calculate_risk(
        attack_name="BENIGN",
        model_confidence=51,
        virustotal_score=15.38,
        abuse_score=100,
    )
    assert result["risk_level"] in {"HIGH", "CRITICAL", "MEDIUM"}
    assert result["cti_reputation_boost"] is True
    assert result["risk_score"] > 40


def test_risk_engine_returns_level():
    engine = RiskEngine()
    result = engine.calculate_risk(
        attack_name="DDoS",
        model_confidence=96,
        virustotal_score=85,
        abuse_score=90,
    )
    assert "risk_score" in result
    assert result["risk_level"] in {"SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
