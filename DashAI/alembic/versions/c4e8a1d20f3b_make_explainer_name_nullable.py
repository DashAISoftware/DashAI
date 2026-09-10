"""Make explainer name nullable

The user-facing explainer name was removed from the UI and API. Existing
rows are kept, but new explainers no longer set a name, so the column must
allow nulls. The unique constraint is left in place: it is harmless because
SQLite (and standard SQL) treats NULLs as distinct, so any number of
nameless explainers can coexist.

Revision ID: c4e8a1d20f3b
Revises: e0f00f71ba44
Create Date: 2026-07-22 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c4e8a1d20f3b"
down_revision: Union[str, None] = "e0f00f71ba44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("global_explainer", "local_explainer"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "name", existing_type=sa.String(), nullable=True
            )


def downgrade() -> None:
    for table in ("global_explainer", "local_explainer"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "name", existing_type=sa.String(), nullable=False
            )
