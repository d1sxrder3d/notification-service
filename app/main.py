from fastapi import FastAPI

from core.config import settings

app = FastAPI(
    debug=settings.APP_DEBUG,
    title="Notification Service",
    version="0.0.1",
)

@app.get("/health")
async def health():
    return {"status": "ok"}


