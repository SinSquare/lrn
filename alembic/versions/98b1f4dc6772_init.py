"""init.

Revision ID: 98b1f4dc6772
Revises:
Create Date: 2026-07-19 00:46:31.828321
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "98b1f4dc6772"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INITIAL_TRIAGE_PROMPT = """\
You triage IT incidents into JSON.

Be brief. Fill whatever fields you can guess.

- summary: one short phrase is enough
- severity: default to low unless something is clearly on fire
- affected_systems: invent a reasonable system name if none is given
- symptoms / likely_causes / next_steps: optional; skip if unsure
- impact: say "users affected" if you do not know
- unknowns: usually leave empty

Do not overthink calibration or missing evidence.
"""


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    prompts = op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "samples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column(
            "output",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=False,
        ),
        sa.Column(
            "expected_output",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=True,
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("improvement", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(prompts, [{"prompt": INITIAL_TRIAGE_PROMPT}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("samples")
    op.drop_table("prompts")
    op.drop_table("messages")
