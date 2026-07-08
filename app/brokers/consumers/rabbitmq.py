import json
from typing import Any

from aio_pika import IncomingMessage, connect_robust
from aio_pika.abc import (
    AbstractQueue,
    AbstractRobustChannel,
    AbstractRobustConnection,
)

from brokers.consumers.base import MessageConsumer, MessageHandler
from core.logging_config import logger


class RabbitMQConsumer(MessageConsumer):
    def __init__(
        self,
        url: str,
        queue_name: str,
        *,
        prefetch_count: int = 1,
        durable: bool = True,
        requeue_on_error: bool = False,
    ):
        self.url = url
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self.durable = durable
        self.requeue_on_error = requeue_on_error

        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractRobustChannel | None = None
        self.queue: AbstractQueue | None = None
        self.consumer_tag: str | None = None

    async def connect(self) -> None:
        if self.connection and not self.connection.is_closed:
            return

        self.connection = await connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        self.queue = await self.channel.declare_queue(
            self.queue_name,
            durable=self.durable,
        )

    async def start(self, handler: MessageHandler) -> None:
        await self.connect()

        if self.queue is None:
            raise RuntimeError("RabbitMQ queue is not initialized")

        self.consumer_tag = await self.queue.consume(
            lambda message: self._handle_message(message, handler),
        )

    async def stop(self) -> None:
        if self.queue and self.consumer_tag:
            await self.queue.cancel(self.consumer_tag)
            self.consumer_tag = None

        if self.channel and not self.channel.is_closed:
            await self.channel.close()

        if self.connection and not self.connection.is_closed:
            await self.connection.close()

        self.queue = None
        self.channel = None
        self.connection = None

    async def _handle_message(
        self,
        message: IncomingMessage,
        handler: MessageHandler,
    ) -> None:
        try:
            payload = self._decode_message(message)
        except ValueError:
            await message.reject(requeue=False)
            return

        logger.info("Received RabbitMQ message {}", message.delivery_tag)
        async with message.process(requeue=self.requeue_on_error):
            await handler(payload)
        logger.info("Acknowledged RabbitMQ message {}", message.delivery_tag)

    @staticmethod
    def _decode_message(message: IncomingMessage) -> dict[str, Any]:
        try:
            payload = json.loads(message.body.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("RabbitMQ message body must be a valid JSON object") from exc

        if not isinstance(payload, dict):
            raise ValueError("RabbitMQ message body must be a JSON object")

        return payload
