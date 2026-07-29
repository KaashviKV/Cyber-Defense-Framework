def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "services" in payload


def test_model_info_endpoint(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["algorithm"] == "Random Forest"
    assert payload["features"] == 78


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    payload = response.get_json()
    assert "total_analyses" in payload
    assert "average_risk" in payload


def test_feature_importance_endpoint(client):
    response = client.get("/feature-importance")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert len(payload["top_features"]) >= 1


def test_versioned_routes_exist(client):
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/model-info").status_code == 200
    assert client.get("/api/v1/metrics").status_code == 200
    assert client.get("/api/v1/feature-importance").status_code == 200


def test_analyze_validation_error_has_code(client):
    response = client.post("/analyze", json={
        "ip_address": "invalid",
        "features": [1.0] * 78,
    })
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["code"] == "INVALID_IP_ADDRESS"
    assert "request_id" in payload


def test_docs_endpoint(client):
    response = client.get("/docs")
    assert response.status_code == 200
