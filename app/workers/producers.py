from dataclasses import dataclass

from workers.tasks import send_notification_task


@dataclass(slots=True, frozen=True)
class CeleryNotificationTaskProducer:
    def enqueue_send_notification(self, notification_id: int) -> None:
        send_notification_task.delay(notification_id)
