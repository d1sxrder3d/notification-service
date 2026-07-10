import asyncio
from datetime import datetime, timezone

from aiosmtplib.errors import SMTPAuthenticationError, SMTPConnectError, SMTPException

from celery_app.app import app
from core.db import celery_db_manager
from core.logging_config import logger
from models.notification import Notification, NotificationStatus
from providers.registry import ProviderNotConfiguredError, provider_registry
from providers.templates_manager import TemplateRenderingError


def _build_failure_reason(notification: Notification, exc: Exception) -> str:
    if isinstance(exc, ProviderNotConfiguredError):
        return f"provider_not_configured:{notification.channel.value}"

    if isinstance(exc, TemplateRenderingError):
        return f"template_render_failed:{notification.template_code}"

    if isinstance(exc, SMTPAuthenticationError):
        return "smtp_authentication_failed"

    if isinstance(exc, SMTPConnectError):
        return "smtp_connection_failed"

    if isinstance(exc, SMTPException):
        return f"smtp_error:{exc.__class__.__name__}"

    return f"unexpected_error:{exc.__class__.__name__}"


@app.task
def send_notification(notification_id: int):
    with celery_db_manager.session() as session:
        try:
            notification = session.get(Notification, notification_id)

            if notification is None:
                logger.error("Notification with id={} was not found", notification_id)
                return

            if notification.status == NotificationStatus.SENT:
                logger.info("Notification with id={} was already sent, skipping..", notification_id)
                return

            if notification.attempts >= notification.max_attempts:
                logger.warning("Notification with id={} has reached max_attempts, status=FAILED", notification_id)
                notification.status = NotificationStatus.FAILED
                notification.failure_reason = "retry_budget_exhausted"

                session.commit()
                return

            notification.status = NotificationStatus.PROCESSING
            notification.attempts = notification.attempts + 1
            notification.failure_reason = None

            session.flush()

            logger.info(
                "Sending notification {} via {} to {}",
                notification.id,
                notification.channel.value,
                notification.recipient,
            )

            provider = provider_registry.get(notification.channel)
            notification.provider_code = provider.code
            send_result = asyncio.run(
                provider.send(
                    recipient=notification.recipient,
                    template_code=notification.template_code,
                    payload=notification.payload,
                ),
            )

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)

            logger.info(
                "Notification {} sent successfully via {} with metadata {}",
                notification.id,
                notification.channel.value,
                send_result.metadata,
            )

            session.commit()
        except Exception as exc:
            if "notification" in locals() and notification is not None:
                notification.status = NotificationStatus.FAILED
                notification.failure_reason = _build_failure_reason(notification, exc)
                session.commit()
            logger.exception(
                "Failed to send notification {} with reason {}",
                notification_id,
                notification.failure_reason if "notification" in locals() and notification is not None else exc.__class__.__name__,
            )
