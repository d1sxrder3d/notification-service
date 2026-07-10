from types import SimpleNamespace

from models.notification import NotificationStatus
from services.notification import NotificationNotFoundError, NotificationRetryNotAllowedError


def test_create_notification_endpoint_returns_created(api_client, api_dependencies):
    created_notification = SimpleNamespace(id=5, status=NotificationStatus.PENDING)
    api_dependencies.service.create_notification.return_value = created_notification

    response = api_client.post(
        "/api/v1/notifications",
        json={
            "user_id": 1,
            "channel": "email",
            "recipient": "user@example.com",
            "template_code": "welcome",
            "payload": {"name": "Alex"},
            "idempotency_key": "api-create-1",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"id": 5, "status": "pending"}


def test_create_notification_endpoint_returns_validation_error(api_client):
    response = api_client.post(
        "/api/v1/notifications",
        json={
            "user_id": 1,
            "channel": "email",
        },
    )

    assert response.status_code == 422


def test_get_notification_endpoint_returns_notification(api_client, api_dependencies, notification_factory):
    notification = notification_factory(id=3, status=NotificationStatus.FAILED)
    api_dependencies.service.get_notification.return_value = notification

    response = api_client.get("/api/v1/notifications/3")

    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["status"] == "failed"


def test_get_notification_endpoint_returns_not_found(api_client, api_dependencies):
    api_dependencies.service.get_notification.side_effect = NotificationNotFoundError("Notification 99 not found")

    response = api_client.get("/api/v1/notifications/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification 99 not found"


def test_retry_notification_endpoint_returns_retried_notification(api_client, api_dependencies):
    retried_notification = SimpleNamespace(id=4, status=NotificationStatus.PENDING)
    api_dependencies.service.retry_notification.return_value = retried_notification

    response = api_client.post("/api/v1/notifications/4/retry")

    assert response.status_code == 200
    assert response.json() == {"id": 4, "status": "pending"}


def test_retry_notification_endpoint_returns_conflict(api_client, api_dependencies):
    api_dependencies.service.retry_notification.side_effect = NotificationRetryNotAllowedError("retry forbidden")

    response = api_client.post("/api/v1/notifications/4/retry")

    assert response.status_code == 409
    assert response.json()["detail"] == "retry forbidden"
