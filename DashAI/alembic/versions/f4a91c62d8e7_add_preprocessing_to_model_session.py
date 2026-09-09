"""add preprocessing columns to model_session

Revision ID: f4a91c62d8e7
Revises: a5f2c71e9d40
Create Date: 2026-09-08 10:00:00.000000

Sessions created before this column existed have no preprocessing, so an
empty/None value means exactly that — no backfill is needed.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a91c62d8e7"
down_revision: Union[str, None] = "a5f2c71e9d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS = [
    ("preprocessing", sa.JSON(), True, None),
    ("input_column_refs", sa.JSON(), True, None),
    ("preprocessing_status", sa.String(), False, "ready"),
    ("preprocessing_error", sa.String(), True, None),
    ("preprocessing_artifacts_path", sa.String(), True, None),
    ("preprocessing_job_id", sa.String(), True, None),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "model_session" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("model_session")}
    for name, col_type, nullable, server_default in _NEW_COLUMNS:
        if name in existing:
            continue
        op.add_column(
            "model_session",
            sa.Column(
                name,
                col_type,
                nullable=nullable,
                server_default=server_default,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "model_session" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("model_session")}
    for name, _, _, _ in _NEW_COLUMNS:
        if name not in existing:
            continue
        op.drop_column("model_session", name)
