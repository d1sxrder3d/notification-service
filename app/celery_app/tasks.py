from datetime import datetime, timezone

from core.logging_config import logger
from models.notification import Notification, NotificationStatus
from core.db import celery_db_manager
from celery_app.app import app



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

                session.commit()
                return

            notification.status = NotificationStatus.SENT
            notification.attempts = notification.attempts + 1

            session.flush()

            logger.info(
                "Sending notification {} via {} to {}",
                notification.id,
                notification.channel.value,
                notification.recipient,
            )

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)

            session.commit()
        except Exception:
            session.rollback()
            raise