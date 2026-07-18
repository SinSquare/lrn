"""SQLModel database tables."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Column, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field as SQLField, SQLModel


class DBPrompt(SQLModel, table=True):
    """Stored LLM system prompt."""

    __tablename__ = "prompts"

    id: int | None = SQLField(default=None, primary_key=True)
    prompt: str
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )


class DBMessage(SQLModel, table=True):
    """Stored input message."""

    __tablename__ = "messages"

    id: int | None = SQLField(default=None, primary_key=True)
    message: str
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )


class DBSample(SQLModel, table=True):
    """Stored triage sample linked to a message and prompt."""

    __tablename__ = "samples"

    id: int | None = SQLField(default=None, primary_key=True)
    message_id: int = SQLField(foreign_key="messages.id")
    prompt_id: int = SQLField(foreign_key="prompts.id")
    output: dict[str, Any] = SQLField(
        sa_column=Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    )
    expected_output: dict[str, Any] | None = SQLField(
        default=None,
        sa_column=Column(
            JSON().with_variant(JSONB(), "postgresql"),
            nullable=True,
        ),
    )
    score: int | None = SQLField(default=None)
    improvement: Decimal | None = SQLField(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True),
    )
    improved_average_score: Decimal | None = SQLField(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True),
    )
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )
    updated_at: datetime | None = SQLField(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
