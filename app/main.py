from fastapi import FastAPI

from api.router import main_router
from core.config import settings
from core.logging_config import setup_logger, setup_uvicorn_loggers

app = FastAPI(
    debug=settings.APP_DEBUG,
    title="Notification Service",
    version="0.0.1",
)

@app.get("/health", tags=["other"])
async def health():
    return {"status": "ok"}

setup_logger()
setup_uvicorn_loggers()

app.include_router(main_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)