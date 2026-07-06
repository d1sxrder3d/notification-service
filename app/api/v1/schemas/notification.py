from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class CreateNotificationRequest(BaseModel):
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str
    scheduled_at: datetime | None = None


class CreateNotificationResponse(BaseModel):
    id: UUID
    status: NotificationStatus


class NotificationResponse(BaseModel):
    id: UUID
    channel: NotificationChannel
    recipient: str
    template_code: str
    payload: dict[str, Any]
    status: NotificationStatus
    attempts: int
    max_attempts: int
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime