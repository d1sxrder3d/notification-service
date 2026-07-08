from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from core.config import settings


class AsyncDatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            **settings.db.engine_options,
        )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self):
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession | Any, Any]:
        async with self.async_session_factory() as session:
            yield session

    async def close(self):
        await self.engine.dispose()

class SyncDatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            **settings.db.engine_options,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        with self.session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def close(self):
        self.engine.dispose()


celery_db_manager: SyncDatabaseManager = SyncDatabaseManager(settings.db.sync_url)

db_manager: AsyncDatabaseManager = AsyncDatabaseManager(settings.db.url)


async def get_db_session():
    async for session in db_manager.get_session():
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
