from celery import Celery

from core.config import settings


celery_app = Celery(
    "notification_service",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=("workers.tasks",),
)

celery_app.conf.update(
    task_default_queue=settings.celery.task_default_queue,
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
)
