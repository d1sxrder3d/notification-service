from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification, NotificationChannel, NotificationStatus
from core.errors import *



@dataclass(slots=True)
class CreateNotificationCommand:
    user_id: int
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any]
    idempotency_key: str
    scheduled_at: datetime | None = None


class NotificationTaskProducer(Protocol):
    def enqueue_send_notification(self, notification_id: int) -> None:
        pass


@dataclass(slots=True)
class NotificationService:
    default_max_attempts: int = 3
    task_producer: NotificationTaskProducer | None = None

    async def create_notification(
        self,
        session: AsyncSession,
        payload: CreateNotificationCommand,
    ) -> Notification:
        try:
            existing = await self._get_by_idempotency_key(session, payload.idempotency_key)
            if existing is not None:
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
            await session.refresh(notification)
        except Exception:
            await session.rollback()
            raise

        self._enqueue_notification_delivery(notification)
        return notification

    def _enqueue_notification_delivery(self, notification: Notification) -> None:
        if self.task_producer is None:
            return

        self.task_producer.enqueue_send_notification(notification.id)

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
            await session.flush()
            await session.commit()
            await session.refresh(notification)
        except Exception:
            await session.rollback()
            raise

        self._enqueue_notification_delivery(notification)
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
