"""Add artifacts_path to explorer

Revision ID: d5b3c8f2a041
Revises: c4e8a1d20f3b
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d5b3c8f2a041"
down_revision: Union[str, None] = "c4e8a1d20f3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "explorer",
        sa.Column("artifacts_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("explorer", "artifacts_path")
