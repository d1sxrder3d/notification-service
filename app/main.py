from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.router import main_router
from core.config import settings
from core.logging_config import logger, setup_logging
from core.metrics import metrics_middleware, metrics_response


setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting {} on {}:{}", settings.APP_NAME, settings.APP_HOST or "0.0.0.0", settings.APP_PORT or 8000)
    yield
    logger.info("Stopping {}", settings.APP_NAME)

app = FastAPI(
    debug=settings.APP_DEBUG,
    title=settings.APP_NAME,
    version="0.0.1",
    lifespan=lifespan,
)
app.middleware("http")(metrics_middleware)


@app.get("/health", tags=["other"])
async def health():
    return {"status": "ok"}


@app.get(settings.metrics.api_path, tags=["other"])
async def metrics():
    return metrics_response()

app.include_router(main_router)


if __name__ == "__main__":
    import uvicorn
    setup_logging()
    uvicorn.run(
        app,
        host=settings.APP_HOST or "0.0.0.0",
        port=settings.APP_PORT or 8000,
        log_config=None,
    )
