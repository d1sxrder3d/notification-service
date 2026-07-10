from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.notification import NotificationStatus
from services.notification import (
    CreateNotificationCommand,
    NotificationRetryNotAllowedError,
    NotificationService,
)


@pytest.mark.anyio
async def test_create_notification_creates_record_and_dispatches_task(
    monkeypatch,
    mock_async_session,
    notification_factory,
):
    service = NotificationService(default_max_attempts=5)
    delay_mock = MagicMock()
    monkeypatch.setattr("services.notification.send_notification.delay", delay_mock)
    monkeypatch.setattr(
        NotificationService,
        "_get_by_idempotency_key",
        AsyncMock(return_value=None),
    )

    refreshed_notification = notification_factory(id=10, status=NotificationStatus.PENDING)

    async def flush_side_effect():
        created_notification = mock_async_session.add.call_args.args[0]
        created_notification.id = refreshed_notification.id

    mock_async_session.flush.side_effect = flush_side_effect

    async def refresh_side_effect(notification):
        notification.id = refreshed_notification.id

    mock_async_session.refresh.side_effect = refresh_side_effect

    result = await service.create_notification(
        session=mock_async_session,
        payload=CreateNotificationCommand(
            user_id=1,
            channel=refreshed_notification.channel,
            recipient=refreshed_notification.recipient,
            template_code=refreshed_notification.template_code,
            payload=refreshed_notification.payload,
            idempotency_key="new-key",
        ),
    )

    created_notification = mock_async_session.add.call_args.args[0]
    assert created_notification.status == NotificationStatus.PENDING
    assert created_notification.max_attempts == 5
    mock_async_session.flush.assert_awaited_once()
    assert mock_async_session.commit.await_count == 1
    delay_mock.assert_called_once_with(notification_id=created_notification.id)
    assert result.id == 10


@pytest.mark.anyio
async def test_create_notification_returns_existing_by_idempotency_key(
    monkeypatch,
    mock_async_session,
    notification_factory,
):
    existing_notification = notification_factory(id=42)
    monkeypatch.setattr(
        NotificationService,
        "_get_by_idempotency_key",
        AsyncMock(return_value=existing_notification),
    )

    service = NotificationService()

    result = await service.create_notification(
        session=mock_async_session,
        payload=CreateNotificationCommand(
            user_id=1,
            channel=existing_notification.channel,
            recipient=existing_notification.recipient,
            template_code=existing_notification.template_code,
            payload=existing_notification.payload,
            idempotency_key=existing_notification.idempotency_key,
        ),
    )

    assert result is existing_notification
    mock_async_session.add.assert_not_called()
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_retry_notification_resets_failure_reason_and_dispatches_task(
    monkeypatch,
    mock_async_session,
    notification_factory,
):
    notification = notification_factory(
        id=7,
        status=NotificationStatus.FAILED,
        attempts=1,
        failure_reason="smtp_connection_failed",
    )
    delay_mock = MagicMock()
    monkeypatch.setattr("services.notification.send_notification.delay", delay_mock)
    monkeypatch.setattr(
        NotificationService,
        "get_notification",
        AsyncMock(return_value=notification),
    )

    service = NotificationService()

    result = await service.retry_notification(
        session=mock_async_session,
        notification_id=7,
    )

    assert result is notification
    assert notification.status == NotificationStatus.PENDING
    assert notification.failure_reason is None
    mock_async_session.flush.assert_awaited_once()
    delay_mock.assert_called_once_with(notification_id=7)


@pytest.mark.anyio
async def test_retry_notification_rejects_sent_notifications(
    monkeypatch,
    mock_async_session,
    notification_factory,
):
    notification = notification_factory(status=NotificationStatus.SENT)
    monkeypatch.setattr(
        NotificationService,
        "get_notification",
        AsyncMock(return_value=notification),
    )

    service = NotificationService()

    with pytest.raises(NotificationRetryNotAllowedError):
        await service.retry_notification(
            session=mock_async_session,
            notification_id=notification.id,
        )


@pytest.mark.anyio
async def test_retry_notification_rejects_exhausted_retry_budget(
    monkeypatch,
    mock_async_session,
    notification_factory,
):
    notification = notification_factory(
        status=NotificationStatus.FAILED,
        attempts=3,
        max_attempts=3,
    )
    monkeypatch.setattr(
        NotificationService,
        "get_notification",
        AsyncMock(return_value=notification),
    )

    service = NotificationService()

    with pytest.raises(NotificationRetryNotAllowedError):
        await service.retry_notification(
            session=mock_async_session,
            notification_id=notification.id,
        )
