from fastapi import APIRouter

from api.v1.routes.notification import notification_router


main_router = APIRouter(prefix="/api")

main_router.include_router(notification_router, prefix="/v1")
