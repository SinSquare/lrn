"""Dashboard response schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ImprovementPoint(BaseModel):
    """One value on the positive score climb."""

    sample_id: int
    created_at: datetime
    value: Decimal
    score: int | None = None
    improvement: Decimal | None = None
    improved_average_score: Decimal | None = None


class ImprovementSeriesResponse(BaseModel):
    """Positive-only climb of improved average scores."""

    points: list[ImprovementPoint] = Field(default_factory=list)
