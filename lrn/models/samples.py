"""GET /samples response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from lrn.models.process import IncidentTriage
from lrn.models.prompts import PaginationMeta


class SampleItem(BaseModel):
    id: int
    message: str
    prompt: str
    output: IncidentTriage
    expected_output: IncidentTriage | None = None
    score: int | None
    created_at: datetime
    updated_at: datetime | None = None


class SamplesResponse(BaseModel):
    """Processed samples newest first, with cursor pagination."""

    samples: list[SampleItem] = Field(default_factory=list)
    meta: PaginationMeta = Field(default_factory=PaginationMeta)
