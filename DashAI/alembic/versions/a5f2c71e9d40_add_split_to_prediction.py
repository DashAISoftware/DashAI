"""add the split column to prediction

Revision ID: a5f2c71e9d40
Revises: b7c1d4e9f206
Create Date: 2026-09-01 10:00:00.000000

Predictions made before this column existed covered the whole dataset, which
is what a null value means, so no backfill is needed.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a5f2c71e9d40"
down_revision: Union[str, None] = "b7c1d4e9f206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "prediction" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("prediction")}
    if "split" in columns:
        return
    op.add_column("prediction", sa.Column("split", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "prediction" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("prediction")}
    if "split" not in columns:
        return
    op.drop_column("prediction", "split")
