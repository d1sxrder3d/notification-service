from fastapi import FastAPI

from core.config import settings
from api.router import main_router
app = FastAPI(
    debug=settings.APP_DEBUG,
    title="Notification Service",
    version="0.0.1",
)

@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(main_router)