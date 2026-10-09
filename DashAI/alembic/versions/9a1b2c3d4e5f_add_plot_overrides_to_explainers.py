"""Add plot_overrides to explainers

Revision ID: 9a1b2c3d4e5f
Revises: f1a2b3c4d5e6
Create Date: 2026-07-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "global_explainer", sa.Column("plot_overrides", sa.JSON(), nullable=True)
    )
    op.add_column(
        "local_explainer", sa.Column("plot_overrides", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("local_explainer", "plot_overrides")
    op.drop_column("global_explainer", "plot_overrides")
