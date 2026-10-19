"""add live stage progress to generative processes

While a generative (RAG) process runs, the chat frontend polls the process and
shows the current pipeline stage. This column carries that live payload — one
of ``{"stage": "transforming"}``, ``{"stage": "retrieving", "queries": [...]}``
or ``{"stage": "generating"}`` — and is set back to NULL once the process
finishes or errors (see ``RAG_constants`` for the exact contract).

Revision ID: n7o8p9q1r2s3
Revises: c5d1a9e74f28
Create Date: 2026-10-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n7o8p9q1r2s3"
down_revision: Union[str, None] = "c5d1a9e74f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("generative_process") as batch_op:
        batch_op.add_column(sa.Column("progress", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("generative_process") as batch_op:
        batch_op.drop_column("progress")
