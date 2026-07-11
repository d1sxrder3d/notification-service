import asyncio
from datetime import datetime, timezone
from time import perf_counter

from aiosmtplib.errors import SMTPAuthenticationError, SMTPConnectError, SMTPException
from celery.exceptions import Retry
from celery.signals import worker_process_init, worker_init
from sqlalchemy import select

from celery_app.app import app
from core.config import settings
from core.db import celery_db_manager
from core.logging_config import logger
from core.metrics import (
    observe_celery_task_failed,
    observe_celery_task_retried,
    observe_celery_task_started,
    observe_celery_task_succeeded,
    observe_notification_delivery_latency,
    observe_notification_failed,
    observe_notification_retried,
    observe_notification_send,
    observe_notification_sent,
    start_metrics_server,
)
from models.notification import Notification, NotificationStatus
from providers.registry import ProviderNotConfiguredError, provider_registry
from providers.templates_manager import TemplateRenderingError


def _normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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

UNRETRIEVABLE_REASONS = ("provider_not_configured",
                         "smtp_authentication_failed",
                         "template_render_failed")

@worker_process_init.connect
def _start_worker_metrics_server(**_: object) -> None:
    start_metrics_server(settings.metrics.celery_port)



@worker_init.connect
def _requeue_pending_notifications(**_: object) -> None:
    """ Worker-init хук, который смотрит в БД при запуске, проверяя её на наличие необработанных задач """
    with celery_db_manager.session() as session:
        try:
            pending_notification_ids = session.execute(
                select(Notification.id).where(Notification.status.in_([NotificationStatus.PENDING]))
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


@app.task(bind=True)
def send_notification(self, notification_id: int):
    task_name = "send_notification"
    observe_celery_task_started(task_name)
    with celery_db_manager.session() as session:
        started_at = perf_counter()
        provider_code = "unassigned"
        channel = "unknown"
        try:
            notification = session.execute(
                select(Notification)
                .where(Notification.id == notification_id)
                .with_for_update()
            ).scalar_one_or_none()

            if notification is None:
                logger.error("Notification with id={} was not found", notification_id)
                observe_celery_task_succeeded(task_name, perf_counter() - started_at)
                return

            if notification.status == NotificationStatus.SENT:
                logger.info("Notification with id={} was already sent, skipping..", notification_id)
                observe_celery_task_succeeded(task_name, perf_counter() - started_at)
                return

            if notification.status == NotificationStatus.PROCESSING:
                logger.info("Notification with id={} is already processing, skipping..", notification_id)
                observe_celery_task_succeeded(task_name, perf_counter() - started_at)
                return

            if notification.attempts >= notification.max_attempts:
                logger.warning("Notification with id={} has reached max_attempts, status=FAILED", notification_id)
                notification.status = NotificationStatus.FAILED
                notification.failure_reason = "retry_budget_exhausted"
                provider_code = notification.provider_code or provider_code
                channel = notification.channel.value
                observe_notification_failed(
                    channel=channel,
                    provider_code=provider_code,
                    reason="retry_budget_exhausted",
                )

                session.commit()
                observe_celery_task_failed(task_name, perf_counter() - started_at)
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
            observe_notification_sent(channel=channel, provider_code=provider_code)
            if notification.created_at is not None:
                created_at = _normalize_utc_datetime(notification.created_at)
                sent_at = _normalize_utc_datetime(notification.sent_at)
                observe_notification_delivery_latency(
                    channel=channel,
                    provider_code=provider_code,
                    latency_seconds=(sent_at - created_at).total_seconds(),
                )

            session.commit()
            observe_celery_task_succeeded(task_name, perf_counter() - started_at)
        except Retry:
            raise
        except Exception as exc:
            if "notification" in locals() and notification is not None:
                failure_reason = _build_failure_reason(notification, exc)

                is_unretrievable = False

                for reason in UNRETRIEVABLE_REASONS:
                    if reason in failure_reason:
                        is_unretrievable = True
                        break

                if notification.attempts < notification.max_attempts and not is_unretrievable:
                    notification.status = NotificationStatus.PENDING
                    notification.failure_reason = failure_reason
                    session.commit()
                    observe_notification_retried(channel)
                    observe_celery_task_retried(task_name, perf_counter() - started_at)

                    logger.warning(
                        "Notification {} failed on attempt {}/{}, retrying",
                        notification.id,
                        notification.attempts,
                        notification.max_attempts,
                    )

                    raise self.retry(exc=exc)

                notification.status = NotificationStatus.FAILED
                notification.failure_reason = failure_reason
                observe_notification_failed(
                    channel=channel,
                    provider_code=provider_code,
                    reason=failure_reason,
                )
                observe_notification_send(
                    channel=channel,
                    provider_code=provider_code,
                    status="failed",
                    duration_seconds=perf_counter() - started_at,
                )
                session.commit()
                observe_celery_task_failed(task_name, perf_counter() - started_at)
            logger.exception(
                "Failed to send notification {} with reason {}",
                notification_id,
                notification.failure_reason if "notification" in locals() and notification is not None else exc.__class__.__name__,
            )
