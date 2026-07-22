"""Tests for the improvement dashboard series."""

from datetime import datetime, timezone
from decimal import Decimal

from lrn.models.db_models import DBMessage, DBPrompt, DBSample
from lrn.routes.dashboard import build_improvement_series
from tests.conftest import _triage_output


def _sample(
    *,
    sample_id: int,
    day: int,
    score: int | None = None,
    improvement: str | None = None,
    improved_average_score: str | None = None,
) -> DBSample:
    return DBSample(
        id=sample_id,
        message_id=1,
        prompt_id=1,
        output=_triage_output(summary=f"Summary {sample_id}"),
        score=score,
        improvement=None if improvement is None else Decimal(improvement),
        improved_average_score=(
            None if improved_average_score is None else Decimal(improved_average_score)
        ),
        created_at=datetime(2026, 1, day, tzinfo=timezone.utc),
    )


def test_build_series_uses_improved_average_as_score_and_includes_improvement():
    samples = [
        _sample(
            sample_id=1,
            day=1,
            score=40,
            improvement="8.00",
            improved_average_score="55.00",
        ),
        _sample(sample_id=2, day=2, score=50, improvement="3.00"),
        _sample(
            sample_id=3,
            day=3,
            score=60,
            improvement="12.00",
            improved_average_score="70.00",
        ),
    ]

    points = build_improvement_series(samples)

    assert [p.sample_id for p in points] == [1, 3]
    assert [p.score for p in points] == [Decimal("55.00"), Decimal("70.00")]
    assert [p.improvement for p in points] == [Decimal("8.00"), Decimal("12.00")]


def test_dashboard_series_endpoint(client, db_session_maker):
    async def _seed() -> None:
        async with db_session_maker() as session:
            prompt = DBPrompt(
                prompt="triage prompt",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
            session.add(prompt)
            await session.flush()
            for i, (score, avg, improvement) in enumerate(
                [
                    (40, None, None),
                    (50, Decimal("58.00"), Decimal("10.00")),
                    (45, Decimal("40.00"), Decimal("-2.00")),
                    (55, Decimal("72.00"), Decimal("5.00")),
                ],
                start=1,
            ):
                message = DBMessage(
                    message=f"message {i}",
                    created_at=datetime(2026, 1, i, tzinfo=timezone.utc),
                )
                session.add(message)
                await session.flush()
                session.add(
                    DBSample(
                        message_id=message.id,  # type: ignore[arg-type]
                        prompt_id=prompt.id,  # type: ignore[arg-type]
                        output=_triage_output(summary=f"Summary {i}"),
                        score=score,
                        improvement=improvement,
                        improved_average_score=avg,
                        created_at=datetime(2026, 1, i, tzinfo=timezone.utc),
                    )
                )
            await session.commit()

    import asyncio

    asyncio.run(_seed())

    resp = client.get("/dashboard/series")
    assert resp.status_code == 200
    body = resp.json()
    # Only improvement > 0 rows (ids 2 and 4); id 1/3 filtered out.
    assert [p["sample_id"] for p in body["points"]] == [2, 4]
    assert [p["score"] for p in body["points"]] == ["58.00", "72.00"]
    assert [p["improvement"] for p in body["points"]] == ["10.00", "5.00"]
    for p in body["points"]:
        assert set(p) == {"sample_id", "created_at", "score", "improvement"}


def test_dashboard_page_served(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert b"chart" in resp.content
    assert b"point-count" in resp.content
    assert b"improvement:" in resp.content
