"""Background review: gold expected output, score vs actual, improved prompt."""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import ValidationError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.llm import compare_outputs, review_message, triage_message
from lrn.models.db_models import DBMessage, DBPrompt, DBSample
from lrn.models.process import IncidentTriage
from lrn.state import get_async_session_maker, get_config

log = logging.getLogger(__name__)


async def _rescore_sample(
    improved_prompt: str,
    message: str,
    expected: IncidentTriage,
) -> int:
    """Triage with the improved prompt and score against expected output."""
    new_actual = await triage_message(improved_prompt, message)
    comparison = await compare_outputs(expected, new_actual)
    return comparison.field_scores.overall()


async def _eval_improved_prompt(
    db: AsyncSession,
    improved_prompt: str,
) -> tuple[int, int, int]:
    """Re-score the last n samples with the improved prompt.

    Returns (original_sum, updated_sum, evaluated_count).
    Uses each sample's expected_output as ground truth.
    """
    config = get_config()
    n = config.review_rescore_limit
    concurrency = config.review_rescore_concurrency
    result = await db.exec(
        select(DBSample, DBMessage)
        .join(DBMessage, DBSample.message_id == DBMessage.id)
        .where(
            col(DBSample.output).is_not(None),
            col(DBSample.score).is_not(None),
            col(DBSample.expected_output).is_not(None),
        )
        .order_by(col(DBSample.id).desc())
        .limit(n)
    )

    candidates: list[tuple[int, str, IncidentTriage]] = []
    for sample, message in result.all():
        try:
            IncidentTriage.model_validate(sample.output)
        except ValidationError:
            log.warning(
                f"Skipping sample {sample.id}: output is not a valid IncidentTriage"
            )
            continue

        try:
            expected = IncidentTriage.model_validate(sample.expected_output)
        except ValidationError:
            log.warning(
                f"Skipping sample #{sample.id}: "
                "expected_output is not a valid IncidentTriage"
            )
            continue

        assert sample.score is not None
        candidates.append((sample.score, message.message, expected))

    if not candidates:
        return 0, 0, 0

    updated_scores: list[int] = []
    for i in range(0, len(candidates), concurrency):
        batch = candidates[i : i + concurrency]
        batch_scores = await asyncio.gather(
            *(
                _rescore_sample(improved_prompt, message, expected)
                for _, message, expected in batch
            )
        )
        updated_scores.extend(batch_scores)

    original_sum = sum(score for score, _, _ in candidates)
    updated_sum = sum(updated_scores)
    return original_sum, updated_sum, len(candidates)


async def review_sample_background(sample_id: int) -> None:
    """Review one sample: expected_output, similarity score, improved prompt."""
    log.info(f"Running background review for sample #{sample_id}")

    session_maker = get_async_session_maker()
    try:
        async with session_maker() as db:
            result = await db.exec(
                select(DBSample, DBMessage, DBPrompt)
                .join(DBMessage, DBSample.message_id == DBMessage.id)
                .join(DBPrompt, DBSample.prompt_id == DBPrompt.id)
                .where(DBSample.id == sample_id)
            )
            row = result.first()
            if row is None:
                log.warning(f"Background review: sample {sample_id} not found")
                return

            sample, message, prompt = row
            review = await review_message(prompt.prompt, message.message)
            actual = IncidentTriage.model_validate(sample.output)
            comparison = await compare_outputs(review.expected_output, actual)
            score = comparison.field_scores.overall()

            sample.expected_output = review.expected_output.model_dump(mode="json")
            sample.score = score
            sample.updated_at = datetime.now(timezone.utc)
            db.add(sample)
            # Flush so this sample is visible when re-scoring the last n.
            await db.flush()

            log.info(f"sample #{sample_id} score={score}")

            improved = review.improved_prompt.strip()
            if improved and improved != prompt.prompt.strip():
                original_sum, updated_sum, evaluated = await _eval_improved_prompt(
                    db, improved
                )
                if original_sum > 0:
                    improvement_pct = (
                        (updated_sum - original_sum) / original_sum
                    ) * 100
                else:
                    improvement_pct = 0.0 if updated_sum == 0 else 100.0
                sample.improvement = Decimal(f"{improvement_pct:.2f}")
                if evaluated > 0:
                    sample.improved_average_score = (
                        Decimal(updated_sum) / Decimal(evaluated)
                    ).quantize(Decimal("0.01"))
                sample.updated_at = datetime.now(timezone.utc)
                db.add(sample)
                if evaluated > 0 and updated_sum > original_sum:
                    db.add(DBPrompt(prompt=review.improved_prompt))
                    log.info(
                        f"Background review #{sample.id}: persisting improved prompt "
                        f"(original_sum={original_sum} updated_sum={updated_sum} "
                        f"evaluated={evaluated} improvement={sample.improvement}%)"
                    )
                else:
                    log.info(
                        f"Background review #{sample.id}: skipping improved prompt "
                        f"(original_sum={original_sum} updated_sum={updated_sum} "
                        f"evaluated={evaluated} improvement={sample.improvement}%)"
                    )

            await db.commit()

    except Exception:
        log.exception(f"Background review failed for sample {sample_id}")
