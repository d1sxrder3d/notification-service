from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.models.notification import NotificationChannel


@dataclass(slots=True, frozen=True)
class ProviderSendResult:
    external_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NotificationProvider(ABC):
    channel: NotificationChannel

    @abstractmethod
    async def send(
        self,
        recipient: str,
        template_code: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        raise NotImplementedError
