"""GET /samples"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.models import db_models
from lrn.models.process import IncidentTriage
from lrn.models.prompts import PaginationMeta
from lrn.models.samples import SampleItem, SamplesResponse
from lrn.state import get_async_db

router = APIRouter()


@router.get(
    "/samples",
    response_model=SamplesResponse,
    status_code=200,
)
async def list_samples(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    from_: Annotated[int | None, Query(alias="from", ge=1)] = None,
) -> SamplesResponse:
    """Browse processed samples newest first, paginated by id cursor."""
    stmt = (
        select(db_models.DBSample, db_models.DBMessage, db_models.DBPrompt)
        .join(
            db_models.DBMessage,
            db_models.DBSample.message_id == db_models.DBMessage.id,
        )
        .join(
            db_models.DBPrompt,
            db_models.DBSample.prompt_id == db_models.DBPrompt.id,
        )
        .order_by(col(db_models.DBSample.id).desc())
    )
    if from_ is not None:
        stmt = stmt.where(db_models.DBSample.id <= from_)
    stmt = stmt.limit(limit + 1)

    result = await db.exec(stmt)
    rows = list(result.all())

    next_id: int | None = None
    if len(rows) > limit:
        next_id = rows[limit][0].id
        rows = rows[:limit]

    items = [
        SampleItem(
            id=sample.id,  # type: ignore[arg-type]
            message=message.message,
            prompt=prompt.prompt,
            output=IncidentTriage.model_validate(sample.output),
            expected_output=(
                IncidentTriage.model_validate(sample.expected_output)
                if sample.expected_output is not None
                else None
            ),
            score=sample.score,
            created_at=sample.created_at,
            updated_at=sample.updated_at,
        )
        for sample, message, prompt in rows
    ]
    return SamplesResponse(
        samples=items,
        meta=PaginationMeta(next_id=next_id),
    )
