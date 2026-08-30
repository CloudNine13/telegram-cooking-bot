from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(database_url: str | None = None) -> AsyncEngine:
    global _engine
    if database_url is not None:
        return create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    global _session_maker
    if engine is not None:
        return async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


@asynccontextmanager
async def get_session(
    session_maker: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    maker: async_sessionmaker[AsyncSession] = session_maker or get_session_maker()
    async with maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
