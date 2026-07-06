from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from base import BaseModel


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(nullable=False)

    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel),
        nullable=False,
    )

    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    template_code: Mapped[str] = mapped_column(String(100), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
    )

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3) # TODO: ВЫНЕСТИ В CONFIG

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )