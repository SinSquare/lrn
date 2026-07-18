"""GET /prompts"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.models import db_models
from lrn.models.prompts import PaginationMeta, PromptItem, PromptsResponse
from lrn.state import get_async_db

router = APIRouter()


@router.get(
    "/prompts",
    response_model=PromptsResponse,
    status_code=200,
)
async def list_prompts(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    from_: Annotated[int | None, Query(alias="from", ge=1)] = None,
) -> PromptsResponse:
    """Return triage prompts newest first, paginated by id cursor."""
    stmt = select(db_models.DBPrompt).order_by(col(db_models.DBPrompt.id).desc())
    if from_ is not None:
        stmt = stmt.where(db_models.DBPrompt.id <= from_)
    stmt = stmt.limit(limit + 1)

    result = await db.exec(stmt)
    rows = list(result.all())

    next_id: int | None = None
    if len(rows) > limit:
        next_id = rows[limit].id
        rows = rows[:limit]

    prompts = [
        PromptItem(id=row.id, prompt=row.prompt, created_at=row.created_at)  # type: ignore[arg-type]
        for row in rows
    ]
    return PromptsResponse(
        prompts=prompts,
        meta=PaginationMeta(next_id=next_id),
    )
