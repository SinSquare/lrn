"""GET /prompts response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PromptItem(BaseModel):
    id: int
    prompt: str
    created_at: datetime


class PaginationMeta(BaseModel):
    """First id of the next page; pass as `from` to continue. Null if none."""

    next_id: int | None = None


class PromptsResponse(BaseModel):
    """Prompt versions newest first, with cursor pagination."""

    prompts: list[PromptItem] = Field(default_factory=list)
    meta: PaginationMeta = Field(default_factory=PaginationMeta)
