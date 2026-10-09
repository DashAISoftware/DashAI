"""add uniqueness constraints to rag tables and fix storage tracing

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Chunk: replace useless (id, document_id) with (document_id, chunk_index, chunking_model_id) ──
    with op.batch_alter_table('chunk', schema=None) as batch_op:
        batch_op.drop_constraint('uix_chunk_document', type_='unique')
        batch_op.create_unique_constraint(
            'uix_document_chunk_index_chunking',
            ['document_id', 'chunk_index', 'chunking_model_id'],
        )

    # ── RAGPrompt ──
    with op.batch_alter_table('rag_prompt', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_prompt_class_params',
            ['class_name', 'parameters'],
        )

    # ── RAGGenerationModel ──
    with op.batch_alter_table('rag_generation_model', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_gen_model_class_params',
            ['class_name', 'parameters'],
        )

    # ── RAGChunkingModel ──
    with op.batch_alter_table('rag_chunking_model', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_chunking_model_class_params',
            ['class_name', 'parameters'],
        )

    # ── RAGEmbeddingModel ──
    with op.batch_alter_table('rag_embedding_model', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_embedding_model_class_params',
            ['class_name', 'parameters'],
        )

    # ── RAGSparseRetriever ──
    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_sparse_retriever',
            ['class_name', 'parameters', 'documents_ids', 'chunking_model_id'],
        )

    # ── RAGDenseRetriever ──
    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uix_rag_dense_retriever',
            ['class_name', 'parameters', 'document_ids',
             'chunking_model_id', 'embedding_model_id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('rag_dense_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_dense_retriever', type_='unique')

    with op.batch_alter_table('rag_sparse_retriever', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_sparse_retriever', type_='unique')

    with op.batch_alter_table('rag_embedding_model', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_embedding_model_class_params', type_='unique')

    with op.batch_alter_table('rag_chunking_model', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_chunking_model_class_params', type_='unique')

    with op.batch_alter_table('rag_generation_model', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_gen_model_class_params', type_='unique')

    with op.batch_alter_table('rag_prompt', schema=None) as batch_op:
        batch_op.drop_constraint('uix_rag_prompt_class_params', type_='unique')

    with op.batch_alter_table('chunk', schema=None) as batch_op:
        batch_op.drop_constraint('uix_document_chunk_index_chunking', type_='unique')
        batch_op.create_unique_constraint(
            'uix_chunk_document',
            ['id', 'document_id'],
        )
