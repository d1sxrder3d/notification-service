def test_metrics_endpoint_returns_prometheus_payload(api_client):
    response = api_client.get("/metrics")

    assert response.status_code == 200
    assert "notification_service_api_requests_total" in response.text
