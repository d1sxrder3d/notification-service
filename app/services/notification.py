from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification, NotificationChannel, NotificationStatus
from celery_app.tasks import send_notification
from core.config import settings
from core.errors import *
from core.logging_config import logger



@dataclass(slots=True)
class CreateNotificationCommand:
    user_id: int
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any]
    idempotency_key: str
    scheduled_at: datetime | None = None



@dataclass(slots=True)
class NotificationService:
    default_max_attempts: int = settings.NOTIFICATION_MAX_ATTEMPTS

    async def create_notification(
        self,
        session: AsyncSession,
        payload: CreateNotificationCommand,
    ) -> Notification:
        try:
            existing = await self._get_by_idempotency_key(session, payload.idempotency_key)
            if existing is not None:
                await session.commit()
                return existing
            notification = Notification(
                user_id=payload.user_id,
                channel=payload.channel,
                recipient=payload.recipient,
                template_code=payload.template_code,
                payload=payload.payload,
                status=NotificationStatus.PENDING,
                attempts=0,
                max_attempts=self.default_max_attempts,
                idempotency_key=payload.idempotency_key,
                scheduled_at=payload.scheduled_at,
            )
            session.add(notification)
            await session.flush()
            await session.commit()

            logger.debug("NOTIF_SERVICE: Notification (id={}) sent to Celery", notification.id)
            send_notification.delay(notification_id=notification.id)

            await session.refresh(notification)

        except Exception:
            await session.rollback()
            raise

        return notification


    @staticmethod
    async def get_notification(
        session: AsyncSession,
        notification_id: int,
    ) -> type[Notification]:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        return notification


    async def retry_notification(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> type[Notification]:
        try:
            notification = await self.get_notification(session, notification_id)

            if notification.status == NotificationStatus.SENT:
                raise NotificationRetryNotAllowedError(
                    f"Notification {notification_id} was already sent",
                )

            if notification.attempts >= notification.max_attempts:
                raise NotificationRetryNotAllowedError(
                    f"Notification {notification_id} exhausted retry budget",
                )

            notification.status = NotificationStatus.PENDING
            notification.sent_at = None
            notification.failure_reason = None
            notification.provider_id = None
            notification.provider_code = None
            await session.flush()
            await session.commit()
            await session.refresh(notification)
            logger.info("NOTIF_SERVICE: Sending notification to CELERY")
            send_notification.delay(notification_id=notification.id)

        except Exception:
            await session.rollback()
            raise

        return notification

    @staticmethod
    async def _get_by_idempotency_key(
        session: AsyncSession,
        idempotency_key: str,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.idempotency_key == idempotency_key,
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
