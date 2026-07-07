import asyncio
from datetime import datetime, timezone

from core.db import db_manager
from core.logging_config import logger, setup_logging
from models.notification import Notification, NotificationStatus
from workers.celery_app import celery_app


@celery_app.task(name="notifications.send")
def send_notification_task(notification_id: int) -> None:
    setup_logging()
    asyncio.run(_send_notification(notification_id))


async def _send_notification(notification_id: int) -> None:
    async with db_manager.session() as session:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            logger.warning("Notification {} not found, skipping send task", notification_id)
            return

        if notification.status == NotificationStatus.SENT:
            logger.info("Notification {} already sent, skipping send task", notification_id)
            return

        if notification.attempts >= notification.max_attempts:
            notification.status = NotificationStatus.FAILED
            logger.warning("Notification {} exhausted retry budget", notification_id)
            return

        notification.status = NotificationStatus.PROCESSING
        notification.attempts += 1
        await session.flush()

        logger.info(
            "Sending notification {} via {} to {}",
            notification.id,
            notification.channel.value,
            notification.recipient,
        )

        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(timezone.utc)
