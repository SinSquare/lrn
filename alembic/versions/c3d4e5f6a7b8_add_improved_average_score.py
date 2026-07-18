"""add sample improved_average_score

Revision ID: c3d4e5f6a7b8
Revises: 98b1f4dc6772
Create Date: 2026-07-19 01:06:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "98b1f4dc6772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "samples",
        sa.Column(
            "improved_average_score",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("samples", "improved_average_score")
