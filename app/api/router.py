from fastapi import APIRouter

from v1.routes.notification import notification_router


main_router = APIRouter(prefix="/api", tags=["api"])

main_router.include_router(notification_router, prefix="/v1", tags=["v1"])
