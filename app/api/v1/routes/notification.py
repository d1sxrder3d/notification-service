from fastapi import status, APIRouter

from app.api.v1.schemas.notification import *


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
    ):

    ...


@notification_router.post(
    '/notifications/{notification_id}/retry',
    tags=["notification"],
    status_code=status.HTTP_200_OK,
    response_model=CreateNotificationResponse
)
async def retry_notification(
        notification_id: int,
    ):
    ...


@notification_router.get(
    "/notifications/{notification_id}",
    tags=["notification"],
    status_code=status.HTTP_200_OK,
    response_model=NotificationResponse
)
async def get_notification(
        notification_id: int,
):
    ...



