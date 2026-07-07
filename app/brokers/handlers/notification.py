from dataclasses import dataclass

from api.v1.schemas.notification import CreateNotificationRequest
from core.db import AsyncDatabaseManager, db_manager
from services.notification import CreateNotificationCommand, NotificationService


@dataclass(slots=True)
class NotificationMessageHandler:
    notification_service: NotificationService
    database_manager: AsyncDatabaseManager = db_manager

    async def __call__(self, message: dict) -> None:
        request = CreateNotificationRequest.model_validate(message)

        async with self.database_manager.async_session_factory() as session:
            await self.notification_service.create_notification(
                session=session,
                payload=CreateNotificationCommand(
                    user_id=request.user_id,
                    channel=request.channel,
                    recipient=request.recipient,
                    template_code=request.template_code,
                    payload=request.payload,
                    idempotency_key=request.idempotency_key,
                    scheduled_at=request.scheduled_at,
                ),
            )
