def test_security_headers(client):
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"


def test_not_found_returns_standard_error(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["code"] == "NOT_FOUND"
    assert "request_id" in payload


def test_model_performance_endpoint(client):
    response = client.get("/model-performance")
    payload = response.get_json()
    assert "request_id" in payload

    if response.status_code == 200:
        assert payload["status"] == "success"
        assert "accuracy" in payload
        assert "f1_score" in payload
    else:
        assert response.status_code == 503
        assert payload["status"] == "error"
        assert payload["code"] in {"EVAL_DATA_MISSING", "MODEL_EVALUATION_FAILED"}


def test_versioned_model_performance(client):
    response = client.get("/api/v1/model-performance")
    assert response.status_code in {200, 503}
