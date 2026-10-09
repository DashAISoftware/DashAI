"""add processed_document_content cache table

Revision ID: g6h7i8j9k0l1
Revises: f6a7b8c9d0e1
Create Date: 2026-08-12 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g6h7i8j9k0l1'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'processed_document_content',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('signature', sa.String(), nullable=False),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_processed_document_content'),
        sa.UniqueConstraint(
            'document_id', 'signature',
            name='uix_processed_document_content_signature'
        ),
    )
    with op.batch_alter_table('processed_document_content', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_processed_document_content_document_id',
            'document',
            ['document_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "processed_document_content" in inspector.get_table_names():
        op.drop_table("processed_document_content")
