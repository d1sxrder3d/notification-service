from typing import Literal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR: Path = Path(__file__).resolve().parent.parent



class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        env_prefix="DB_",
    )

    type: Literal['sqlite', "postgres"] = "sqlite"

    sqlite_path: Path = BASE_DIR / "data" / "notification_service.db"

    host: str = "localhost"
    port: int = 5432
    name: str = "app_db"
    user: str = "root"
    password: str = "root"

    echo: bool = False
    pool_pre_ping: bool = False

    @property
    def alembic_url(self) -> str:
        if self.type == "postgres":
            return (
                f"postgresql+asyncpg://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )

        Path(BASE_DIR / 'data').mkdir(parents=True, exist_ok=True)

        return f"sqlite+aiosqlite:///{self.sqlite_path.as_posix()}"

    @property
    def url(self) -> str:
        if self.type == "postgres":
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"sqlite+aiosqlite:///{self.sqlite_path}"

    @property
    def engine_options(self) -> dict:
        options = {"echo": self.echo}

        if self.type == "postgres":
            options.update({
                "pool_size": 5,
                "max_overflow": 10,
                "pool_pre_ping": True,
            })

        return options


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        env_prefix="CELERY_",
    )

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    task_default_queue: str = "notification_tasks"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: tuple[str, ...] = ("json",)
    timezone: str = "UTC"

class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        env_prefix="RMQ_",
    )

    url: str = "amqp://guest:guest@localhost:5672/"
    queue_name: str = "notifications"
    prefetch_count: int = 1
    durable: bool = True
    requeue_on_error: bool = False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
    )

    APP_NAME: str = "Notification Service"
    APP_DEBUG: bool = True
    APP_HOST: str = ""
    APP_PORT: int = 0

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOGS_DIR: Path = BASE_DIR / "logs"
    NOTIFICATION_MAX_ATTEMPTS: int = 3

    db: DBSettings = DBSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    celery: CelerySettings = CelerySettings()


settings = Settings()

