"""GET /dashboard — simple improvement climb chart."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lrn.models import db_models
from lrn.models.dashboard import ImprovementPoint, ImprovementSeriesResponse
from lrn.state import get_async_db

router = APIRouter()

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def build_improvement_series(
    samples: list[db_models.DBSample],
) -> list[ImprovementPoint]:
    """Build series points from samples with improved averages.

    Y value is improved_average_score; improvement is included for display.
    """
    points: list[ImprovementPoint] = []

    for sample in samples:
        assert sample.id is not None
        if sample.improved_average_score is None:
            continue
        points.append(
            ImprovementPoint(
                sample_id=sample.id,
                created_at=sample.created_at,
                value=sample.improved_average_score,
                score=sample.score,
                improvement=sample.improvement,
                improved_average_score=sample.improved_average_score,
            )
        )

    return points


@router.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    """Serve the dashboard HTML page."""
    return FileResponse(_STATIC_DIR / "dashboard.html")


@router.get(
    "/dashboard/series",
    response_model=ImprovementSeriesResponse,
    status_code=200,
)
async def improvement_series(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> ImprovementSeriesResponse:
    """Return the positive improvement climb over time."""
    result = await db.exec(
        select(db_models.DBSample)
        .where(
            col(db_models.DBSample.improvement).is_not(None),
            col(db_models.DBSample.improvement) > 0,
        )
        .order_by(col(db_models.DBSample.created_at).asc())
    )
    samples = list(result.all())
    return ImprovementSeriesResponse(points=build_improvement_series(samples))
