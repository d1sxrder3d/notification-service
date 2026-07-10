from __future__ import annotations

from time import perf_counter
from typing import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest, start_http_server


api_requests_total = Counter(
    "notification_service_api_requests_total",
    "Total number of API requests",
    ("method", "path", "status"),
)

api_request_duration_seconds = Histogram(
    "notification_service_api_request_duration_seconds",
    "API request duration in seconds",
    ("method", "path"),
)

notifications_created_total = Counter(
    "notification_service_notifications_created_total",
    "Total number of created notifications",
    ("channel",),
)

notifications_retried_total = Counter(
    "notification_service_notifications_retried_total",
    "Total number of retried notifications",
    ("channel",),
)

notification_send_total = Counter(
    "notification_service_notification_send_total",
    "Total number of notification send attempts",
    ("channel", "provider_code", "status"),
)

notification_send_duration_seconds = Histogram(
    "notification_service_notification_send_duration_seconds",
    "Notification send duration in seconds",
    ("channel", "provider_code", "status"),
)

provider_send_total = Counter(
    "notification_service_provider_send_total",
    "Total number of provider send calls",
    ("channel", "provider_code", "status"),
)

provider_send_duration_seconds = Histogram(
    "notification_service_provider_send_duration_seconds",
    "Provider send duration in seconds",
    ("channel", "provider_code"),
)

rabbitmq_messages_total = Counter(
    "notification_service_rabbitmq_messages_total",
    "Total number of RabbitMQ messages processed",
    ("status",),
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def start_metrics_server(port: int) -> None:
    start_http_server(port)


def observe_api_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    status_str = str(status)
    api_requests_total.labels(method=method, path=path, status=status_str).inc()
    api_request_duration_seconds.labels(method=method, path=path).observe(duration_seconds)


def observe_notification_created(channel: str) -> None:
    notifications_created_total.labels(channel=channel).inc()


def observe_notification_retried(channel: str) -> None:
    notifications_retried_total.labels(channel=channel).inc()


def observe_notification_send(
    channel: str,
    provider_code: str,
    status: str,
    duration_seconds: float,
) -> None:
    notification_send_total.labels(
        channel=channel,
        provider_code=provider_code,
        status=status,
    ).inc()
    notification_send_duration_seconds.labels(
        channel=channel,
        provider_code=provider_code,
        status=status,
    ).observe(duration_seconds)


def observe_provider_send(
    channel: str,
    provider_code: str,
    status: str,
    duration_seconds: float,
) -> None:
    provider_send_total.labels(
        channel=channel,
        provider_code=provider_code,
        status=status,
    ).inc()
    provider_send_duration_seconds.labels(
        channel=channel,
        provider_code=provider_code,
    ).observe(duration_seconds)


def observe_rabbitmq_message(status: str) -> None:
    rabbitmq_messages_total.labels(status=status).inc()


async def metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route is not None else request.url.path
    observe_api_request(
        method=request.method,
        path=path,
        status=response.status_code,
        duration_seconds=perf_counter() - started_at,
    )
    return response
