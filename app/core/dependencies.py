from core.config import settings
from services.notification import NotificationService
from functools import lru_cache

@lru_cache
def get_notification_service() -> NotificationService:
    return NotificationService(
        default_max_attempts=settings.NOTIFICATION_MAX_ATTEMPTS,
    )
