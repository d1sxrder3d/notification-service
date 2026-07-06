import logging
import sys
from pathlib import Path

from loguru import logger

from core.config import settings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

SIMPLE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logs_dir = Path(settings.LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    is_debug = settings.APP_DEBUG
    console_level = "DEBUG" if is_debug else settings.LOG_LEVEL
    console_format = LOG_FORMAT if is_debug else SIMPLE_FORMAT

    logger.add(
        sys.stdout,
        format=console_format,
        level=console_level,
        colorize=is_debug,
        enqueue=True,
        backtrace=is_debug,
        diagnose=is_debug,
    )

    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.log",
        format=LOG_FORMAT,
        level=settings.LOG_LEVEL,
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=is_debug,
        diagnose=is_debug,
    )

    logger.add(
        logs_dir / "errors_{time:YYYY-MM-DD}.log",
        format=LOG_FORMAT,
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    intercept_handler = InterceptHandler()

    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [intercept_handler]
        uvicorn_logger.propagate = False


__all__ = ("logger", "setup_logging")
