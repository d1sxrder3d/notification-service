from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from models.notification import NotificationChannel, NotificationStatus


class CreateNotificationRequest(BaseModel):
    user_id: int
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str
    scheduled_at: datetime | None = None


class CreateNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: NotificationStatus


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any]
    status: NotificationStatus
    attempts: int
    max_attempts: int
    provider_id: int | None
    provider_code: str | None
    failure_reason: str | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
