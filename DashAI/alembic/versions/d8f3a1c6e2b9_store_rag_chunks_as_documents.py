"""store RAG chunks as documents

Chunk text moves from the ``chunk`` table to Arrow files written per chunk set
and document, so ``rag_chunk_set_document`` gains the folder and the chunk
count. Existing chunk sets lose their owning session: the startup cleanup
deletes chunk sets without a session together with their retrievers,
embeddings and files, and sessions are indexed again on demand.

This migration performs no filesystem I/O.

Revision ID: d8f3a1c6e2b9
Revises: c5d1a9e74f28
Create Date: 2026-10-15
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d8f3a1c6e2b9"
down_revision: Union[str, None] = "c5d1a9e74f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("chunk")
    with op.batch_alter_table("rag_chunk_set_document") as batch_op:
        batch_op.add_column(sa.Column("path", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("n_chunks", sa.Integer(), nullable=True))
    op.execute("UPDATE rag_chunk_set SET session_id = NULL")


def downgrade() -> None:
    with op.batch_alter_table("rag_chunk_set_document") as batch_op:
        batch_op.drop_column("n_chunks")
        batch_op.drop_column("path")
    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_set_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["chunk_set_id"],
            ["rag_chunk_set.id"],
            name="fk_chunk_chunk_set_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["data_document.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chunk_set_id",
            "document_id",
            "chunk_index",
            name="uix_chunk_set_doc_index",
        ),
    )
