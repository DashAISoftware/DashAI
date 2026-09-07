"""invert FK direction for retrievers and add rag_retriever_child

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop old FK from RAGPipeline to RAGRetriever ──
    with op.batch_alter_table('rag_pipeline', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_rag_pipeline_retriever_model_id_rag_retriever', type_='foreignkey'
        )
        batch_op.drop_column('retriever_model_id')

    # ── Rebuild RAGRetriever: drop old columns, add pipeline_id ──
    with op.batch_alter_table('rag_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('chk_retriever_type', type_='check')
        batch_op.drop_constraint(
            'fk_rag_retriever_dense_retriever_id_rag_dense_retriever', type_='foreignkey'
        )
        batch_op.drop_constraint(
            'fk_rag_retriever_sparse_retriever_id_rag_sparse_retriever', type_='foreignkey'
        )
        batch_op.drop_column('dense_retriever_id')
        batch_op.drop_column('sparse_retriever_id')
        batch_op.drop_column('composite_child_ids')
        batch_op.add_column(
            sa.Column('pipeline_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_retriever_pipeline_id',
            'rag_pipeline', ['pipeline_id'], ['id'], ondelete='CASCADE',
        )

    # ── Add bridge_id to RAGSparseRetriever ──
    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('bridge_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_sparse_retriever_bridge_id',
            'rag_retriever', ['bridge_id'], ['id'], ondelete='CASCADE',
        )

    # ── Add bridge_id to RAGDenseRetriever ──
    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('bridge_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_dense_retriever_bridge_id',
            'rag_retriever', ['bridge_id'], ['id'], ondelete='CASCADE',
        )

    # ── Create RAGRetrieverChild ──
    op.create_table(
        'rag_retriever_child',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('child_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['parent_id'], ['rag_retriever.id'],
            name='fk_rag_retriever_child_parent', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['child_id'], ['rag_retriever.id'],
            name='fk_rag_retriever_child_child', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_rag_retriever_child'),
        sa.UniqueConstraint(
            'parent_id', 'child_order',
            name='uix_retriever_child_order',
        ),
    )


def downgrade() -> None:
    op.drop_table('rag_retriever_child')

    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('fk_rag_dense_retriever_bridge_id', type_='foreignkey')
        batch_op.drop_column('bridge_id')

    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('fk_rag_sparse_retriever_bridge_id', type_='foreignkey')
        batch_op.drop_column('bridge_id')

    with op.batch_alter_table('rag_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('fk_rag_retriever_pipeline_id', type_='foreignkey')
        batch_op.drop_column('pipeline_id')
        batch_op.add_column(
            sa.Column('composite_child_ids', sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('sparse_retriever_id', sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('dense_retriever_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_rag_retriever_sparse_retriever_id_rag_sparse_retriever',
            'rag_sparse_retriever', ['sparse_retriever_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_foreign_key(
            'fk_rag_retriever_dense_retriever_id_rag_dense_retriever',
            'rag_dense_retriever', ['dense_retriever_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_check_constraint(
            'chk_retriever_type',
            'NOT (dense_retriever_id IS NOT NULL AND sparse_retriever_id IS NOT NULL)',
        )

    with op.batch_alter_table('rag_pipeline', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('retriever_model_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_pipeline_retriever_model_id_rag_retriever',
            'rag_retriever', ['retriever_model_id'], ['id'], ondelete='CASCADE',
        )
