import asyncio
from datetime import datetime, timezone
from time import perf_counter

from aiosmtplib.errors import SMTPAuthenticationError, SMTPConnectError, SMTPException
from celery.signals import worker_process_init, worker_init
from sqlalchemy import select

from celery_app.app import app
from core.config import settings
from core.db import celery_db_manager
from core.logging_config import logger
from core.metrics import observe_notification_send, start_metrics_server
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


@worker_process_init.connect
def _start_worker_metrics_server(**_: object) -> None:
    start_metrics_server(settings.metrics.celery_port)



@worker_init.connect
def _requeue_pending_notifications(**_: object) -> None:
    with celery_db_manager.session() as session:
        try:
            pending_notification_ids = session.execute(
                select(Notification.id).where(Notification.status == NotificationStatus.PENDING)
            ).scalars().all()

            if not pending_notification_ids:
                logger.info("No pending notifications found on celery startup")
                return

            logger.warning(
                "Found {} pending notifications on celery startup, requeueing",
                len(pending_notification_ids),
            )

            for notification_id in pending_notification_ids:
                send_notification.delay(notification_id)
        except Exception:
            logger.exception("Failed to requeue pending notifications on celery startup")


@app.task
def send_notification(notification_id: int):
    with celery_db_manager.session() as session:
        started_at = perf_counter()
        provider_code = "unassigned"
        channel = "unknown"
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
            channel = notification.channel.value

            logger.info(
                "Sending notification {} via {} to {}",
                notification.id,
                notification.channel.value,
                notification.recipient,
            )

            provider = provider_registry.get(notification.channel)
            notification.provider_code = provider.code
            provider_code = provider.code
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
            observe_notification_send(
                channel=channel,
                provider_code=provider_code,
                status="sent",
                duration_seconds=perf_counter() - started_at,
            )

            session.commit()
        except Exception as exc:
            if "notification" in locals() and notification is not None:
                notification.status = NotificationStatus.FAILED
                notification.failure_reason = _build_failure_reason(notification, exc)
                observe_notification_send(
                    channel=channel,
                    provider_code=provider_code,
                    status="failed",
                    duration_seconds=perf_counter() - started_at,
                )
                session.commit()
            logger.exception(
                "Failed to send notification {} with reason {}",
                notification_id,
                notification.failure_reason if "notification" in locals() and notification is not None else exc.__class__.__name__,
            )
