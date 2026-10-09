"""add rag_extractor table and replace document.extractor JSON with FK

Revision ID: f6a7b8c9d0e1
Revises: c8d4e0f2a6b3
Create Date: 2026-08-12 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'c8d4e0f2a6b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create rag_extractor table
    op.create_table(
        'rag_extractor',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('component_name', sa.String(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_rag_extractor'),
    )

    # 2. Add extractor_id FK to document (SQLite batch mode) and drop the old
    #    JSON extractor column if it exists. The extractor column is only
    #    present when the now-deleted e5f6a7b8c9d0 migration was ever applied.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    document_columns = {
        col["name"] for col in inspector.get_columns("document")
    }

    with op.batch_alter_table('document', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('extractor_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_document_extractor_id',
            'rag_extractor',
            ['extractor_id'],
            ['id'],
            ondelete='SET NULL',
        )
        if 'extractor' in document_columns:
            batch_op.drop_column('extractor')


def downgrade() -> None:
    with op.batch_alter_table('document', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('extractor', sa.JSON(), nullable=True)
        )
        batch_op.drop_constraint('fk_document_extractor_id', type_='foreignkey')
        batch_op.drop_column('extractor_id')

    op.drop_table('rag_extractor')
