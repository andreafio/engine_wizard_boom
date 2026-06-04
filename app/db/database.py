"""Async SQLAlchemy engine and session factory."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _normalize_db_url(url: str) -> str:
    """Converte postgres:// e postgresql:// nel formato richiesto da asyncpg."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_engine():
    global _engine
    if _engine is None and settings.database_url:
        _engine = create_async_engine(
            _normalize_db_url(settings.database_url),
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    global _session_factory
    engine = get_engine()
    if _session_factory is None and engine:
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def init_db() -> None:
    """Create all tables if DATABASE_URL is configured."""
    engine = get_engine()
    if engine is None:
        logger.info("db_skipped", reason="DATABASE_URL not set")
        return
    # Import models so Base knows about them
    from app.db import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("db_initialized")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    if factory is None:
        return
    async with factory() as session:
        yield session
