from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.db import get_db_session
from core.dependencies import get_notification_service
from main import app
from models.base import BaseModel
from models.notification import Notification, NotificationChannel, NotificationStatus


@pytest.fixture
def templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "app" / "templates"


@pytest.fixture
def notification_factory():
    def factory(**overrides):
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "user_id": 1,
            "channel": NotificationChannel.EMAIL,
            "recipient": "user@example.com",
            "template_code": "welcome",
            "payload": {"name": "Alex"},
            "status": NotificationStatus.PENDING,
            "attempts": 0,
            "max_attempts": 3,
            "idempotency_key": "test-key",
            "provider_code": None,
            "failure_reason": None,
            "scheduled_at": None,
            "sent_at": None,
            "created_at": now,
            "updated_at": now,
        }
        data.update(overrides)
        return Notification(**data)

    return factory


@pytest.fixture
def mock_async_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def api_dependencies():
    service = AsyncMock()
    session = AsyncMock()

    async def override_get_db_session():
        yield session

    def override_get_notification_service():
        return service

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_notification_service] = override_get_notification_service

    yield SimpleNamespace(service=service, session=session)

    app.dependency_overrides.clear()


@pytest.fixture
def sqlite_session_factory(tmp_path):
    db_path = tmp_path / "test_notifications.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(BaseModel.metadata.create_all)

    async def teardown():
        await engine.dispose()

    return SimpleNamespace(
        engine=engine,
        session_factory=session_factory,
        setup=setup,
        teardown=teardown,
    )


@pytest.fixture
def sync_session_context():
    @contextmanager
    def factory(session):
        yield session

    return factory
