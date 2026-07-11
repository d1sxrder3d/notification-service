from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiosmtplib.errors import SMTPAuthenticationError
from celery.exceptions import Retry

from celery_app.tasks import send_notification
from models.notification import NotificationStatus
from providers.registry import ProviderNotConfiguredError
from providers.templates_manager import TemplateRenderingError


def _build_session(notification):
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = notification
    return session


def test_send_notification_marks_as_sent_on_success(
    monkeypatch,
    notification_factory,
    sync_session_context,
):
    notification = notification_factory(status=NotificationStatus.PENDING)
    session = _build_session(notification)

    provider = MagicMock()
    provider.id = 11
    provider.code = "smtp_primary"
    provider.send = AsyncMock(return_value=MagicMock(metadata={"smtp_response": "ok"}))

    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))
    monkeypatch.setattr("celery_app.tasks.provider_registry.get", MagicMock(return_value=provider))

    send_notification(notification.id)

    assert notification.status == NotificationStatus.SENT
    assert notification.provider_code == "smtp_primary"
    assert notification.failure_reason is None
    assert notification.attempts == 1
    session.commit.assert_called()


def test_send_notification_handles_naive_created_at_for_delivery_latency(
    monkeypatch,
    notification_factory,
    sync_session_context,
):
    notification = notification_factory(
        status=NotificationStatus.PENDING,
        created_at=datetime(2026, 7, 11, 12, 0, 0),
    )
    session = _build_session(notification)

    provider = MagicMock()
    provider.code = "smtp_primary"
    provider.send = AsyncMock(return_value=MagicMock(metadata={"smtp_response": "ok"}))

    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))
    monkeypatch.setattr("celery_app.tasks.provider_registry.get", MagicMock(return_value=provider))

    send_notification(notification.id)

    assert notification.status == NotificationStatus.SENT
    session.commit.assert_called()


def test_send_notification_marks_budget_exhausted_failure(
    monkeypatch,
    notification_factory,
    sync_session_context,
):
    notification = notification_factory(
        attempts=3,
        max_attempts=3,
        status=NotificationStatus.PENDING,
    )
    session = _build_session(notification)

    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))

    send_notification(notification.id)

    assert notification.status == NotificationStatus.FAILED
    assert notification.failure_reason == "retry_budget_exhausted"


@pytest.mark.parametrize(
    ("exception", "expected_reason"),
    [
        (TemplateRenderingError("bad template"), "template_render_failed:welcome"),
        (ProviderNotConfiguredError("missing"), "provider_not_configured:email"),
        (SMTPAuthenticationError(535, "bad auth"), "smtp_authentication_failed"),
    ],
)
def test_send_notification_saves_failure_reason_on_errors(
    monkeypatch,
    notification_factory,
    sync_session_context,
    exception,
    expected_reason,
):
    notification = notification_factory(status=NotificationStatus.PENDING)
    session = _build_session(notification)

    provider = MagicMock()
    provider.id = 1
    provider.code = "smtp_primary"
    provider.send = AsyncMock(side_effect=exception)

    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))

    if isinstance(exception, ProviderNotConfiguredError):
        monkeypatch.setattr(
            "celery_app.tasks.provider_registry.get",
            MagicMock(side_effect=exception),
        )
    else:
        monkeypatch.setattr(
            "celery_app.tasks.provider_registry.get",
            MagicMock(return_value=provider),
        )

    send_notification(notification.id)

    assert notification.status == NotificationStatus.FAILED
    assert notification.failure_reason == expected_reason
    session.commit.assert_called()


def test_send_notification_retries_on_retriable_error(
    monkeypatch,
    notification_factory,
    sync_session_context,
):
    notification = notification_factory(status=NotificationStatus.PENDING)
    session = _build_session(notification)

    provider = MagicMock()
    provider.code = "smtp_primary"
    provider.send = AsyncMock(side_effect=ValueError("boom"))

    retry_mock = MagicMock(side_effect=Retry())

    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))
    monkeypatch.setattr("celery_app.tasks.provider_registry.get", MagicMock(return_value=provider))
    monkeypatch.setattr(send_notification, "retry", retry_mock)

    with pytest.raises(Retry):
        send_notification(notification.id)

    assert notification.status == NotificationStatus.PENDING
    assert notification.failure_reason == "unexpected_error:ValueError"
    retry_mock.assert_called_once()
    session.commit.assert_called()


def test_send_notification_skips_already_sent_notifications(
    monkeypatch,
    notification_factory,
    sync_session_context,
):
    notification = notification_factory(status=NotificationStatus.SENT)
    session = _build_session(notification)

    provider_get = MagicMock()
    monkeypatch.setattr("celery_app.tasks.celery_db_manager.session", lambda: sync_session_context(session))
    monkeypatch.setattr("celery_app.tasks.provider_registry.get", provider_get)

    send_notification(notification.id)

    provider_get.assert_not_called()
    assert notification.status == NotificationStatus.SENT
