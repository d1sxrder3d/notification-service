from typing import Literal, Any
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR: Path = Path(__file__).resolve().parent.parent

# ---- ----  Providers ---- ----

class SMTPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        env_prefix="SMTP_",
    )

    channel: str = "email"

    host: str = "smtp.gmail.com"
    port: int = 465

    username: str = "username@example.com"
    password: str = "password12345"

    sender_email: str = "username@gmail.com"
    sender_name: str = "Notification Service"

    use_tls: bool = False
    start_tls: bool = True

# ---- ----  Providers ---- ----

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
    name: str = "notification_service"
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
    def sync_url(self) -> str:
        if self.type == "postgres":
            return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"sqlite:///{self.sqlite_path.as_posix()}"


    @property
    def engine_options(self) -> dict:
        options: dict[str, Any] = {"echo": self.echo}

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
    broker_host: str = "localhost"
    broker_port: int = 6379
    broker_db: int = 0

    result_host: str = "localhost"
    result_port: int = 6379
    result_db: int = 1

    task_default_queue: str = "notification_tasks"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: tuple[str, ...] = ("json",)
    timezone: str = "UTC"

    @property
    def get_broker_url(self):
        return f"redis://{self.broker_host}:{self.broker_port}/{self.broker_db}"

    @property
    def get_result_backend(self):
        return f"redis://{self.result_host}:{self.result_port}/{self.result_db}"


class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        env_prefix="RMQ_",
    )

    protocol: Literal["amqp", "amqps"] = "amqp"
    user: str = "guest"
    password: str = "guest"
    host: str = "localhost"
    port: int = 5672
    # format: "/.../"
    vhost: str = "/"

    queue_name: str = "notifications"
    prefetch_count: int = 1
    durable: bool = True
    requeue_on_error: bool = False

    @property
    def get_url(self):
        return f"{self.protocol}://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"


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
    TEMPLATES_DIR: Path = BASE_DIR / "templates"

    NOTIFICATION_MAX_ATTEMPTS: int = 3

    db: DBSettings = DBSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    celery: CelerySettings = CelerySettings()
    smtp: SMTPSettings = SMTPSettings()


settings = Settings()

