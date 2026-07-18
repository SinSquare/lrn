"""POST /process"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.llm import triage_message
from lrn.models import db_models
from lrn.models.db_models import DBPrompt
from lrn.models.process import IncidentTriage, ProcessRequest
from lrn.review import review_sample_background
from lrn.state import get_async_db, get_config
from lrn.errors import NotFound, ApiException

router = APIRouter()


async def _get_prompt(db: AsyncSession) -> DBPrompt:
    result = await db.exec(
        select(db_models.DBPrompt)
        .order_by(col(db_models.DBPrompt.created_at).desc())
        .limit(1)
    )
    prompt_row = result.first()
    if prompt_row is None:
        raise NotFound(message="No prompt found")

    return prompt_row


@router.post(
    "/process",
    response_model=IncidentTriage,
    status_code=200,
)
async def process_message(
    data: ProcessRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    background_tasks: BackgroundTasks,
) -> IncidentTriage:
    if not get_config().gemini_api_key:
        raise ApiException(status_code=500, message="Gemini API key is not configured")

    prompt = await _get_prompt(db)
    triage = await triage_message(prompt.prompt, data.message)

    message_row = db_models.DBMessage(message=data.message)
    db.add(message_row)
    await db.flush()

    sample_row = db_models.DBSample(
        message_id=message_row.id,  # type: ignore[arg-type]
        prompt_id=prompt.id,  # type: ignore[arg-type]
        output=triage.model_dump(mode="json"),
    )
    db.add(sample_row)
    await db.commit()
    await db.refresh(sample_row)

    background_tasks.add_task(review_sample_background, sample_row.id)

    return triage
