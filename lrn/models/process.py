"""POST /process request and triage schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    message: str = Field(min_length=10, max_length=2000)


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentTriage(BaseModel):
    summary: str
    severity: Severity
    affected_systems: list[str] = Field(min_length=1)
    symptoms: list[str] = Field(min_length=1)
    likely_causes: list[str] = Field(min_length=1)
    impact: str
    next_steps: list[str] = Field(min_length=1)
    unknowns: list[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    """Gold triage plus an improved system prompt for the same task."""

    expected_output: IncidentTriage
    improved_prompt: str


class FieldScores(BaseModel):
    """Per-field similarity scores for IncidentTriage (0 = unlike, 100 = same)."""

    summary: int = Field(ge=0, le=100)
    severity: int = Field(ge=0, le=100)
    affected_systems: int = Field(ge=0, le=100)
    symptoms: int = Field(ge=0, le=100)
    likely_causes: int = Field(ge=0, le=100)
    impact: int = Field(ge=0, le=100)
    next_steps: int = Field(ge=0, le=100)
    unknowns: int = Field(ge=0, le=100)

    def overall(self) -> int:
        values = [
            self.summary,
            self.severity,
            self.affected_systems,
            self.symptoms,
            self.likely_causes,
            self.impact,
            self.next_steps,
            self.unknowns,
        ]
        return round(sum(values) / len(values))


class ComparisonResult(BaseModel):
    """LLM field-by-field comparison of actual vs expected triage."""

    field_scores: FieldScores
