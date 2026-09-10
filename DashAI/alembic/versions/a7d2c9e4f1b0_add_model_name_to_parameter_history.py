"""Add model_name to parameter_history

Revision ID: a7d2c9e4f1b0
Revises: d4e8a2c6f0b1
Create Date: 2026-07-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a7d2c9e4f1b0"
down_revision: Union[str, None] = "d4e8a2c6f0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("parameter_history", schema=None) as batch_op:
        batch_op.add_column(sa.Column("model_name", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("parameter_history", schema=None) as batch_op:
        batch_op.drop_column("model_name")
