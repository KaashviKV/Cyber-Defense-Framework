from backend.models.analysis_model import build_api_status, enrich_analysis_document


def test_build_api_status_marks_cti_errors():
    status = build_api_status({
        "virustotal": {"error": 401},
        "abuseipdb": {"ip": "8.8.8.8", "abuse_confidence": 10},
    })
    assert status["virustotal"] == "error"
    assert status["abuseipdb"] == "ok"


def test_enrich_analysis_document_adds_schema_metadata():
    doc = enrich_analysis_document({
        "ip_address": "8.8.8.8",
        "virustotal": {"malicious": 0},
        "abuseipdb": {"abuse_confidence": 0},
    })
    assert doc["schema_version"] == "1.0"
    assert doc["api_version"] == "v1"
    assert "timestamp" in doc
    assert "api_status" in doc
