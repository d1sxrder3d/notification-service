import asyncio
import signal
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from brokers.handlers.notification import NotificationMessageHandler
from brokers.consumers.rabbitmq import RabbitMQConsumer
from core.config import settings
from core.db import db_manager
from core.dependencies import get_notification_service
from core.logging_config import logger, setup_logging


def _register_shutdown_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        loop.call_soon_threadsafe(stop_event.set)

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(signal_name, lambda *_: request_shutdown())
        except ValueError:
            logger.warning("Cannot register {} handler in current thread", signal_name.name)


async def run_consumer() -> None:
    setup_logging()

    stop_event = asyncio.Event()
    _register_shutdown_handlers(stop_event)

    consumer = RabbitMQConsumer(
        url=settings.rabbitmq.get_url,
        queue_name=settings.rabbitmq.queue_name,
        prefetch_count=settings.rabbitmq.prefetch_count,
        durable=settings.rabbitmq.durable,
        requeue_on_error=settings.rabbitmq.requeue_on_error,
    )
    handler = NotificationMessageHandler(
        notification_service=get_notification_service(),
    )

    try:
        logger.info(
            "Starting RabbitMQ consumer for queue '{}'",
            settings.rabbitmq.queue_name,
        )
        await consumer.start(handler)
        await stop_event.wait()
    finally:
        logger.info("Stopping RabbitMQ consumer")
        await consumer.stop()
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_consumer())
