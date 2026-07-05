from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from app.core.config import settings


class AsyncDatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,

            echo=False,
            pool_size=10,

            max_overflow=20,

            pool_pre_ping = True,
            pool_recycle = 3600
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


db_manager = AsyncDatabaseManager(settings.db.url)


async def get_db_session():
    async for session in db_manager.get_session():
        yield session
