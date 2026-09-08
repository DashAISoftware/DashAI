"""add chunk_set architecture: chunk_set, chunk_set_document, retriever_chunk_set

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── RAGChunkSet ──
    op.create_table(
        'rag_chunk_set',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('signature', sa.String(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_rag_chunk_set'),
        sa.UniqueConstraint('signature', name='uq_rag_chunk_set_signature'),
    )

    # ── RAGChunkSetDocument ──
    op.create_table(
        'rag_chunk_set_document',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chunk_set_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['chunk_set_id'], ['rag_chunk_set.id'],
            name='fk_chunk_set_doc_set', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['document_id'], ['document.id'],
            name='fk_chunk_set_doc_document', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_rag_chunk_set_document'),
        sa.UniqueConstraint(
            'chunk_set_id', 'document_id', name='uix_chunk_set_document',
        ),
    )

    # ── Chunk: replace chunking_model_id with chunk_set_id, add metadata ──
    with op.batch_alter_table('chunk', schema=None) as batch_op:
        batch_op.drop_constraint('uix_document_chunk_index_chunking', type_='unique')
        batch_op.drop_constraint(
            'fk_chunk_chunking_model_id_rag_chunking_model', type_='foreignkey'
        )
        batch_op.drop_column('chunking_model_id')
        batch_op.add_column(
            sa.Column('chunk_set_id', sa.Integer(), nullable=False)
        )
        batch_op.add_column(
            sa.Column('metadata', sa.JSON(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_chunk_chunk_set_id',
            'rag_chunk_set', ['chunk_set_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_chunk_set_doc_index',
            ['chunk_set_id', 'document_id', 'chunk_index'],
        )

    # ── RAGSparseRetriever: drop documents_ids + chunking_model_id, add chunk_set_id ──
    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_sparse_retriever', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_sparse_retriever_chunking_model_id_rag_chunking_model',
            type_='foreignkey',
        )
        batch_op.drop_column('documents_ids')
        batch_op.drop_column('chunking_model_id')
        batch_op.add_column(
            sa.Column('chunk_set_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_sparse_retriever_chunk_set_id',
            'rag_chunk_set', ['chunk_set_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_rag_sparse_retriever',
            ['class_name', 'parameters', 'chunk_set_id'],
        )

    # ── RAGDenseRetriever: drop document_ids + chunking_model_id, add chunk_set_id ──
    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_dense_retriever', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_dense_retriever_chunking_model_id_rag_chunking_model',
            type_='foreignkey',
        )
        batch_op.drop_column('document_ids')
        batch_op.drop_column('chunking_model_id')
        batch_op.add_column(
            sa.Column('chunk_set_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_dense_retriever_chunk_set_id',
            'rag_chunk_set', ['chunk_set_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_rag_dense_retriever',
            ['class_name', 'parameters', 'chunk_set_id', 'embedding_model_id'],
        )

    # ── RAGEmbeddingMatrix: chunking_model_id → chunk_set_id ──
    with op.batch_alter_table('rag_embedding_matrix', schema=None) as batch_op:
        batch_op.drop_constraint('uix_document_chunking_embedding', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_embedding_matrix_chunking_model_id_rag_chunking_model',
            type_='foreignkey',
        )
        batch_op.drop_column('chunking_model_id')
        batch_op.add_column(
            sa.Column('chunk_set_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_embedding_matrix_chunk_set_id',
            'rag_chunk_set', ['chunk_set_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_document_chunk_set_embedding',
            ['document_id', 'chunk_set_id', 'embedding_model_id'],
        )

    # ── RAGRetrieverChunkSet ──
    op.create_table(
        'rag_retriever_chunk_set',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('retriever_id', sa.Integer(), nullable=False),
        sa.Column('chunk_set_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['retriever_id'], ['rag_retriever.id'],
            name='fk_retriever_chunk_set_retriever', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['chunk_set_id'], ['rag_chunk_set.id'],
            name='fk_retriever_chunk_set_chunk_set', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_rag_retriever_chunk_set'),
        sa.UniqueConstraint(
            'retriever_id', 'chunk_set_id', name='uix_retriever_chunk_set',
        ),
    )


def downgrade() -> None:
    op.drop_table('rag_retriever_chunk_set')

    with op.batch_alter_table('rag_embedding_matrix', schema=None) as batch_op:
        batch_op.drop_constraint('uix_document_chunk_set_embedding', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_embedding_matrix_chunk_set_id', type_='foreignkey',
        )
        batch_op.drop_column('chunk_set_id')
        batch_op.add_column(
            sa.Column('chunking_model_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_rag_embedding_matrix_chunking_model_id_rag_chunking_model',
            'rag_chunking_model', ['chunking_model_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_document_chunking_embedding',
            ['document_id', 'chunking_model_id', 'embedding_model_id'],
        )

    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_dense_retriever', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_dense_retriever_chunk_set_id', type_='foreignkey',
        )
        batch_op.drop_column('chunk_set_id')
        batch_op.add_column(sa.Column('chunking_model_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('document_ids', sa.JSON(), nullable=False))
        batch_op.create_foreign_key(
            'fk_rag_dense_retriever_chunking_model_id_rag_chunking_model',
            'rag_chunking_model', ['chunking_model_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_rag_dense_retriever',
            ['class_name', 'parameters', 'document_ids',
             'chunking_model_id', 'embedding_model_id'],
        )

    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_sparse_retriever', type_='unique')
        batch_op.drop_constraint(
            'fk_rag_sparse_retriever_chunk_set_id', type_='foreignkey',
        )
        batch_op.drop_column('chunk_set_id')
        batch_op.add_column(sa.Column('chunking_model_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('documents_ids', sa.JSON(), nullable=False))
        batch_op.create_foreign_key(
            'fk_rag_sparse_retriever_chunking_model_id_rag_chunking_model',
            'rag_chunking_model', ['chunking_model_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_rag_sparse_retriever',
            ['class_name', 'parameters', 'documents_ids', 'chunking_model_id'],
        )

    with op.batch_alter_table('chunk', schema=None) as batch_op:
        batch_op.drop_constraint('uix_chunk_set_doc_index', type_='unique')
        batch_op.drop_constraint('fk_chunk_chunk_set_id', type_='foreignkey')
        batch_op.drop_column('chunk_set_id')
        batch_op.drop_column('metadata')
        batch_op.add_column(sa.Column('chunking_model_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            'fk_chunk_chunking_model_id_rag_chunking_model',
            'rag_chunking_model', ['chunking_model_id'], ['id'], ondelete='CASCADE',
        )
        batch_op.create_unique_constraint(
            'uix_document_chunk_index_chunking',
            ['document_id', 'chunk_index', 'chunking_model_id'],
        )

    op.drop_table('rag_chunk_set_document')
    op.drop_table('rag_chunk_set')
