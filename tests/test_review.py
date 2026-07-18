"""Tests for background review with mocked LLM calls."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import col, select

from lrn.models.db_models import DBMessage, DBPrompt, DBSample
from lrn.review import review_sample_background
from tests.conftest import _triage_output, make_comparison, make_review, make_triage


async def _seed_sample(
    session_maker,
    *,
    prompt_text: str = "original prompt",
    score: int | None = None,
    expected_output: dict | None = None,
    output_summary: str = "Actual summary",
) -> int:
    async with session_maker() as session:
        prompt = DBPrompt(
            prompt=prompt_text,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session.add(prompt)
        await session.flush()
        message = DBMessage(
            message="checkout is broken and payments fail for all users",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session.add(message)
        await session.flush()
        sample = DBSample(
            message_id=message.id,  # type: ignore[arg-type]
            prompt_id=prompt.id,  # type: ignore[arg-type]
            output=_triage_output(summary=output_summary),
            expected_output=expected_output,
            score=score,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session.add(sample)
        await session.commit()
        await session.refresh(sample)
        assert sample.id is not None
        return sample.id


@pytest.mark.asyncio
async def test_review_missing_sample_does_not_commit(db_session_maker):
    with (
        patch("lrn.review.get_async_session_maker", return_value=db_session_maker),
        patch("lrn.review.review_message", new=AsyncMock()) as review_mock,
    ):
        await review_sample_background(999)

    review_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_review_sets_score_expected_output_and_updated_at(db_session_maker):
    sample_id = await _seed_sample(db_session_maker)
    expected = make_triage(summary="Expected gold summary")
    review = make_review(
        improved_prompt="original prompt",  # same as current → skip improve path
        expected=expected,
    )

    with (
        patch("lrn.review.get_async_session_maker", return_value=db_session_maker),
        patch("lrn.review.review_message", new=AsyncMock(return_value=review)),
        patch(
            "lrn.review.compare_outputs",
            new=AsyncMock(return_value=make_comparison(85)),
        ),
    ):
        await review_sample_background(sample_id)

    async with db_session_maker() as session:
        sample = await session.get(DBSample, sample_id)
        assert sample is not None
        assert sample.score == 85
        assert sample.expected_output == expected.model_dump(mode="json")
        assert sample.updated_at is not None
        assert sample.improvement is None


@pytest.mark.asyncio
async def test_review_persists_improved_prompt_when_rescore_improves(db_session_maker):
    sample_id = await _seed_sample(
        db_session_maker,
        prompt_text="original prompt",
        score=50,
        expected_output=_triage_output(summary="Prior expected"),
    )
    review = make_review(improved_prompt="better prompt v2")

    with (
        patch("lrn.review.get_async_session_maker", return_value=db_session_maker),
        patch("lrn.review.get_config") as get_config,
        patch("lrn.review.review_message", new=AsyncMock(return_value=review)),
        patch(
            "lrn.review.compare_outputs",
            new=AsyncMock(
                side_effect=[
                    make_comparison(60),  # score current sample
                    make_comparison(90),  # rescore candidate(s)
                ]
            ),
        ),
        patch(
            "lrn.review.triage_message",
            new=AsyncMock(return_value=make_triage(summary="Rescored")),
        ),
    ):
        get_config.return_value.review_rescore_limit = 10
        get_config.return_value.review_rescore_concurrency = 5
        await review_sample_background(sample_id)

    async with db_session_maker() as session:
        sample = await session.get(DBSample, sample_id)
        assert sample is not None
        assert sample.score == 60
        assert sample.improvement is not None
        assert float(sample.improvement) > 0
        assert sample.improved_average_score == Decimal("90.00")

        prompts = (
            await session.exec(select(DBPrompt).order_by(col(DBPrompt.id).desc()))
        ).all()
        assert prompts[0].prompt == "better prompt v2"


@pytest.mark.asyncio
async def test_review_skips_improved_prompt_when_rescore_does_not_improve(
    db_session_maker,
):
    sample_id = await _seed_sample(
        db_session_maker,
        prompt_text="original prompt",
        score=80,
        expected_output=_triage_output(summary="Prior expected"),
    )
    review = make_review(improved_prompt="worse prompt")

    with (
        patch("lrn.review.get_async_session_maker", return_value=db_session_maker),
        patch("lrn.review.get_config") as get_config,
        patch("lrn.review.review_message", new=AsyncMock(return_value=review)),
        patch(
            "lrn.review.compare_outputs",
            new=AsyncMock(
                side_effect=[
                    make_comparison(70),
                    make_comparison(40),
                ]
            ),
        ),
        patch(
            "lrn.review.triage_message",
            new=AsyncMock(return_value=make_triage()),
        ),
    ):
        get_config.return_value.review_rescore_limit = 10
        get_config.return_value.review_rescore_concurrency = 5
        await review_sample_background(sample_id)

    async with db_session_maker() as session:
        prompts = (await session.exec(select(DBPrompt))).all()
        assert [p.prompt for p in prompts] == ["original prompt"]
        sample = await session.get(DBSample, sample_id)
        assert sample is not None
        assert sample.improvement is not None
        assert float(sample.improvement) < 0
        assert sample.improved_average_score == Decimal("40.00")


@pytest.mark.asyncio
async def test_review_skips_improve_path_when_prompt_unchanged(db_session_maker):
    sample_id = await _seed_sample(db_session_maker, prompt_text="same prompt")
    review = make_review(improved_prompt="  same prompt  ")

    with (
        patch("lrn.review.get_async_session_maker", return_value=db_session_maker),
        patch("lrn.review.review_message", new=AsyncMock(return_value=review)),
        patch(
            "lrn.review.compare_outputs",
            new=AsyncMock(return_value=make_comparison(75)),
        ),
        patch("lrn.review._eval_improved_prompt", new=AsyncMock()) as eval_mock,
    ):
        await review_sample_background(sample_id)

    eval_mock.assert_not_awaited()
