"""Application dependencies and state."""

import functools
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.config import Config

log = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Ensure lrn.* INFO logs show under uvicorn/fastapi run.

    Uvicorn configures only its own loggers; app loggers otherwise hit
    Python's lastResort handler which drops anything below WARNING.
    """
    package_log = logging.getLogger("lrn")
    if package_log.handlers:
        package_log.setLevel(logging.INFO)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    package_log.addHandler(handler)
    package_log.setLevel(logging.INFO)
    package_log.propagate = False


@functools.lru_cache()
def get_config() -> Config:
    """Return the config loaded from envvars."""
    return Config()


def _async_database_url(url: str) -> str:
    """Derive an async SQLAlchemy URL from the configured sync database URL."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


@functools.lru_cache()
def get_async_engine() -> AsyncEngine:
    """Return a cached async SQLAlchemy engine."""
    config = get_config()
    return create_async_engine(
        _async_database_url(config.db_url),
        pool_pre_ping=True,
        echo=False,
    )


@functools.lru_cache()
def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return a cached async session factory."""
    return async_sessionmaker(
        get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session for FastAPI dependency injection."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session


async def _ensure_schema() -> None:
    """Create tables if needed (migrations own seed data)."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    """Application lifespan."""
    _configure_logging()
    await _ensure_schema()
    yield
    await get_async_engine().dispose()
