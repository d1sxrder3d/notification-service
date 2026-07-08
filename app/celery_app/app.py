from celery import Celery

from core.config import settings

app = Celery(
    'notification_tasks',
    broker_url=settings.celery.get_broker_url,
    result_backend=settings.celery.get_result_backend,
    broker_connection_retry_on_startup=True,
    include=['celery_app.tasks'],
)



