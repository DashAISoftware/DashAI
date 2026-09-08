"""add composite retriever support

Revision ID: a1b2c3d4e5f6
Revises: f928e0b5203d
Create Date: 2026-05-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f928e0b5203d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('rag_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('chk_retriever_type', type_='check')
        batch_op.add_column(
            sa.Column('composite_child_ids', sa.JSON(), nullable=True)
        )
        batch_op.create_check_constraint(
            'chk_retriever_type',
            'NOT (dense_retriever_id IS NOT NULL AND sparse_retriever_id IS NOT NULL)'
        )


def downgrade() -> None:
    with op.batch_alter_table('rag_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('chk_retriever_type', type_='check')
        batch_op.drop_column('composite_child_ids')
        batch_op.create_check_constraint(
            'chk_retriever_type',
            (
                "(class_name = 'SparseRetriever' "
                "AND sparse_retriever_id IS NOT NULL "
                "AND dense_retriever_id IS NULL) OR "
                "(class_name = 'DenseRetriever' "
                "AND dense_retriever_id IS NOT NULL "
                "AND sparse_retriever_id IS NULL)"
            )
        )
