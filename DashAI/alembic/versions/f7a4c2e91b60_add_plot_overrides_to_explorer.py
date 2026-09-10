"""Add plot_overrides to explorer

Revision ID: f7a4c2e91b60
Revises: d5b3c8f2a041
Create Date: 2026-08-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f7a4c2e91b60"
down_revision: Union[str, None] = "d5b3c8f2a041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("explorer", sa.Column("plot_overrides", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("explorer", "plot_overrides")
