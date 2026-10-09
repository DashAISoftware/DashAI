"""make rag_pipeline FK columns nullable

SetupService._ensure_db_record() creates a placeholder RAG_pipeline row
whose FK columns are NULL and patched later in _update_db_record(). The
ORM already models these columns as nullable; this migration aligns the
database schema with that design.

Note: the downgrade re-applies NOT NULL and will fail on databases that
already contain placeholder rows with NULL FKs. Downgrading a populated
RAG database is therefore destructive and unsupported; migrate forward
only.

Revision ID: e9f8a7b6c5d4
Revises: 8d5416cac8f1
Create Date: 2026-08-02 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9f8a7b6c5d4'
down_revision: Union[str, None] = '8d5416cac8f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('rag_pipeline', schema=None) as batch_op:
        batch_op.alter_column(
            'chunking_model_id',
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            'prompt_id',
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            'generation_model_id',
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table('rag_pipeline', schema=None) as batch_op:
        batch_op.alter_column(
            'generation_model_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            'prompt_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            'chunking_model_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
