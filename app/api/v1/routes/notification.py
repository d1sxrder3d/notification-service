from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.schemas.notification import (
    CreateNotificationRequest,
    CreateNotificationResponse,
    NotificationResponse,
)

from core.dependencies import get_notification_service
from core.db import get_db_session
from services.notification import (
    CreateNotificationCommand,
    NotificationNotFoundError,
    NotificationRetryNotAllowedError,
    NotificationService
)

notification_router = APIRouter(
    tags=["notification"],
)


@notification_router.post(
    "/notifications",
    tags=["notification"],
    status_code=status.HTTP_201_CREATED,
    response_model=CreateNotificationResponse
)
async def create_notification(
        notification: CreateNotificationRequest,
        session: AsyncSession = Depends(get_db_session),
        notification_service: NotificationService = Depends(get_notification_service)
    ):
    created_notification = await notification_service.create_notification(
        session=session,
        payload=CreateNotificationCommand(
            user_id=notification.user_id,
            channel=notification.channel,
            recipient=notification.recipient,
            template_code=notification.template_code,
            payload=notification.payload,
            idempotency_key=notification.idempotency_key,
            scheduled_at=notification.scheduled_at,
        ),
    )
    return CreateNotificationResponse.model_validate(created_notification)


@notification_router.post(
    '/notifications/{notification_id}/retry',
    tags=["notification"],
    status_code=status.HTTP_200_OK,
    response_model=CreateNotificationResponse,
)
async def retry_notification(
        notification_id: int,
        session: AsyncSession = Depends(get_db_session),
        notification_service: NotificationService = Depends(get_notification_service)
    ):
    try:
        notification = await notification_service.retry_notification(
            session=session,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotificationRetryNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return CreateNotificationResponse.model_validate(notification)


@notification_router.get(
    "/notifications/{notification_id}",
    tags=["notification"],
    status_code=status.HTTP_200_OK,
    response_model=NotificationResponse
)
async def get_notification(
        notification_id: int,
        session: AsyncSession = Depends(get_db_session),
        notification_service: NotificationService = Depends(get_notification_service)
    ):
    try:
        notification = await notification_service.get_notification(
            session=session,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return NotificationResponse.model_validate(notification)

