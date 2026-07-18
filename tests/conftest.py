"""Shared pytest fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.main import app
from lrn.models.db_models import DBMessage, DBPrompt, DBSample
from lrn.models.process import (
    ComparisonResult,
    FieldScores,
    IncidentTriage,
    ReviewResult,
    Severity,
)
from lrn.state import get_async_db


def make_triage(**overrides) -> IncidentTriage:
    base = dict(
        summary="Portal login fails after MFA for undergrads.",
        severity=Severity.high,
        affected_systems=["Student portal"],
        symptoms=["Redirect after MFA"],
        likely_causes=["Session/cache issue"],
        impact="Many support tickets; registration soon.",
        next_steps=["Check Redis latency"],
        unknowns=["Whether finance is related"],
    )
    base.update(overrides)
    return IncidentTriage.model_validate(base)


def make_comparison(score: int = 80) -> ComparisonResult:
    return ComparisonResult(
        field_scores=FieldScores(
            summary=score,
            severity=score,
            affected_systems=score,
            symptoms=score,
            likely_causes=score,
            impact=score,
            next_steps=score,
            unknowns=score,
        )
    )


def make_review(
    *,
    improved_prompt: str = "improved triage prompt",
    expected: IncidentTriage | None = None,
) -> ReviewResult:
    return ReviewResult(
        expected_output=expected or make_triage(summary="Expected gold summary"),
        improved_prompt=improved_prompt,
    )


def _triage_output(**overrides) -> dict:
    return make_triage(**overrides).model_dump(mode="json")


@pytest.fixture
def db_session_maker() -> Iterator[async_sessionmaker[AsyncSession]]:
    """In-memory SQLite session factory with app tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(_setup())
    try:
        yield session_maker
    finally:
        asyncio.run(engine.dispose())


@pytest.fixture
def client(db_session_maker: async_sessionmaker[AsyncSession]) -> Iterator[TestClient]:
    """HTTP client with DB dependency overridden to in-memory SQLite."""

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_session_maker() as session:
            yield session

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.dependency_overrides[get_async_db] = override_db
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    with TestClient(app) as test_client:
        yield test_client
    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


@pytest.fixture
def seed_prompts(db_session_maker: async_sessionmaker[AsyncSession]) -> list[DBPrompt]:
    """Insert five prompts with ids 1..5 (newest last by id)."""

    async def _seed() -> list[DBPrompt]:
        async with db_session_maker() as session:
            rows: list[DBPrompt] = []
            for i in range(1, 6):
                row = DBPrompt(
                    prompt=f"prompt-{i}",
                    created_at=datetime(2026, 1, i, tzinfo=timezone.utc),
                )
                session.add(row)
                rows.append(row)
            await session.commit()
            for row in rows:
                await session.refresh(row)
            return rows

    return asyncio.run(_seed())


@pytest.fixture
def seed_samples(db_session_maker: async_sessionmaker[AsyncSession]) -> list[DBSample]:
    """Insert five samples with ids 1..5 (newest last by id)."""

    async def _seed() -> list[DBSample]:
        async with db_session_maker() as session:
            prompt = DBPrompt(
                prompt="triage prompt",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
            session.add(prompt)
            await session.flush()

            samples: list[DBSample] = []
            for i in range(1, 6):
                message = DBMessage(
                    message=f"sample message number {i} with enough text",
                    created_at=datetime(2026, 1, i, tzinfo=timezone.utc),
                )
                session.add(message)
                await session.flush()
                sample = DBSample(
                    message_id=message.id,  # type: ignore[arg-type]
                    prompt_id=prompt.id,  # type: ignore[arg-type]
                    output=_triage_output(summary=f"Summary for sample {i}"),
                    expected_output=None,
                    score=None,
                    created_at=datetime(2026, 1, i, tzinfo=timezone.utc),
                    updated_at=None,
                )
                session.add(sample)
                samples.append(sample)
            await session.commit()
            for sample in samples:
                await session.refresh(sample)
            return samples

    return asyncio.run(_seed())
