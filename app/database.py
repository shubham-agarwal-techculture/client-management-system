"""Async database engine, session factory, and base model helpers."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create the async engine. `echo` is driven by DEBUG so SQL is visible in dev.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # SQLite needs `check_same_thread=False` when used with aiosqlite + multiple tasks.
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

# Session factory — do not share sessions across requests.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a short-lived AsyncSession per request."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables defined on Base.metadata.

    Intended for dev/test bootstrapping. Prefer `alembic upgrade head` for
    production schema management.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    """Dispose the engine connection pool (useful in tests / shutdown)."""
    await engine.dispose()