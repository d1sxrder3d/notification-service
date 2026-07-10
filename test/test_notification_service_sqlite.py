from unittest.mock import MagicMock

import pytest

from models.notification import NotificationChannel, NotificationStatus
from services.notification import CreateNotificationCommand, NotificationService


@pytest.mark.anyio
async def test_notification_service_sqlite_preserves_idempotency(
    monkeypatch,
    sqlite_session_factory,
):
    await sqlite_session_factory.setup()
    monkeypatch.setattr("services.notification.send_notification.delay", MagicMock())

    try:
        async with sqlite_session_factory.session_factory() as session:
            service = NotificationService(default_max_attempts=4)
            command = CreateNotificationCommand(
                user_id=1,
                channel=NotificationChannel.EMAIL,
                recipient="user@example.com",
                template_code="welcome",
                payload={"name": "Alex"},
                idempotency_key="sqlite-idempotency-1",
            )

            first = await service.create_notification(session=session, payload=command)
            second = await service.create_notification(session=session, payload=command)

            assert first.id == second.id
            assert first.status == NotificationStatus.PENDING
            assert first.max_attempts == 4
    finally:
        await sqlite_session_factory.teardown()
