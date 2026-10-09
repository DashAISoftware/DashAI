"""Add input_dataset_path to local_explainer

Revision ID: d1c2b3a4f5e6
Revises: 9a1b2c3d4e5f
Create Date: 2026-07-15 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d1c2b3a4f5e6"
down_revision: Union[str, None] = "9a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "local_explainer",
        sa.Column("input_dataset_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("local_explainer", "input_dataset_path")
