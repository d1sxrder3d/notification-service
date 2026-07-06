import sys
from loguru import logger
from typing import Literal
import logging

from core.config import settings

LOGS_DIR = settings.LOGS_DIR

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

SIMPLE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"


def setup_logger(mode: Literal["dev", "debug", "prod"] = "dev"):

    logger.remove()

    if mode == "dev":
        logger.add(
            sys.stdout,
            format=LOG_FORMAT,
            level="DEBUG",
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    elif mode == "debug":

        logger.add(
            sys.stdout,
            format=LOG_FORMAT,
            level="DEBUG",
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

        logger.add(
            LOGS_DIR / "debug_{time:YYYY-MM-DD}.log",
            format=LOG_FORMAT,
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    elif mode == "prod":
        logger.add(
            sys.stdout,
            format=SIMPLE_FORMAT,
            level="INFO",
            colorize=False,
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )

        logger.add(
            LOGS_DIR / "app_{time:YYYY-MM-DD}.log",
            format=LOG_FORMAT,
            level="INFO",
            rotation="50 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
        )

        logger.add(
            LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
            format=LOG_FORMAT,
            level="ERROR",
            rotation="10 MB",
            retention="90 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    # logger.info(f"Logger initialized in {mode.upper()} mode")
    return logger


LOGS_DIR.mkdir(exist_ok=True)

setup_logger(settings.LOG_LEVEL)

def setup_uvicorn_loggers():

    uvicorn_loggers = ["uvicorn", "uvicorn.error", "uvicorn.access"]

    for logger_name in uvicorn_loggers:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = False

    # logger.add(
    #     sys.stdout,
    #     format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    #     level="INFO",
    #     colorize=True,
    # )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for logger_name in uvicorn_loggers:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]


class InterceptHandler(logging.Handler):

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
