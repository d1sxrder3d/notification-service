from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

MessagePayload = dict[str, Any]
MessageHandler = Callable[[MessagePayload], Awaitable[None]]


class MessageConsumer(ABC):

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def start(self, handler: MessageHandler) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

