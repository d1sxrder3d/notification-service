def test_metrics_endpoint_returns_prometheus_payload(api_client):
    response = api_client.get("/metrics")

    assert response.status_code == 200
    assert "notification_service_api_requests_total" in response.text
    assert "notification_service_notifications_sent_total" in response.text
    assert "notification_service_notifications_failed_total" in response.text
    assert "notification_service_notification_delivery_latency_seconds" in response.text
    assert "notification_service_provider_errors_total" in response.text
    assert "notification_service_celery_tasks_started_total" in response.text
