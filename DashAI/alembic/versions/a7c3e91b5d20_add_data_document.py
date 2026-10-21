"""add data_document table

Revision ID: a7c3e91b5d20
Revises: f4a91c62d8e7
Create Date: 2026-10-02 12:00:00.000000

Persistent documents uploaded through the Data module. The session-scoped
RAG ``document`` table is left as is; a later revision replaces it.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e91b5d20"
down_revision: Union[str, None] = "f4a91c62d8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "data_document"
_STATUS = sa.Enum(
    "NOT_STARTED",
    "DELIVERED",
    "STARTED",
    "FINISHED",
    "ERROR",
    name="documentstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("file_hash", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("dataloader", sa.String(), nullable=True),
        sa.Column("dataloader_params", sa.JSON(), nullable=True),
        sa.Column("content_counts", sa.JSON(), nullable=True),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("huey_id", sa.String(), nullable=True),
        sa.Column("status", _STATUS, nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folder.id"],
            name=op.f("fk_data_document_folder_id_folder"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_document")),
        sa.UniqueConstraint("name", name=op.f("uq_data_document_name")),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _TABLE not in sa.inspect(bind).get_table_names():
        return
    op.drop_table(_TABLE)
