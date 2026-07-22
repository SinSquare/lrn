"""Dashboard response schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ImprovementPoint(BaseModel):
    """One score point with its improvement."""

    sample_id: int
    created_at: datetime
    score: Decimal
    improvement: Decimal | None = None


class ImprovementSeriesResponse(BaseModel):
    """Series of improved average scores."""

    points: list[ImprovementPoint] = Field(default_factory=list)
