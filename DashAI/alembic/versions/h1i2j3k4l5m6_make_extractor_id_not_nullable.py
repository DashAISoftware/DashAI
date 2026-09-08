"""make extractor_id not nullable

Revision ID: h1i2j3k4l5m6
Revises: g6h7i8j9k0l1
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, None] = 'g6h7i8j9k0l1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT_EXTRACTORS = {
    "pdf": "PyMuPDFExtractor",
    "txt": "PlainTextExtractor",
    "md": "PlainTextExtractor",
    "rst": "PlainTextExtractor",
    "tex": "PlainTextExtractor",
    "csv": "PlainTextExtractor",
}


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Get all documents with NULL extractor_id
    rows = conn.execute(
        sa.text("SELECT id, file_type FROM document WHERE extractor_id IS NULL")
    ).fetchall()

    # 2. For each, create a RAGExtractor record and set extractor_id
    for doc_id, file_type in rows:
        comp_name = _DEFAULT_EXTRACTORS.get(file_type)
        if comp_name is None:
            continue
        result = conn.execute(
            sa.text(
                "INSERT INTO rag_extractor (component_name, params) "
                "VALUES (:name, '{}')"
            ),
            {"name": comp_name},
        )
        extractor_id = result.lastrowid
        conn.execute(
            sa.text("UPDATE document SET extractor_id = :eid WHERE id = :did"),
            {"eid": extractor_id, "did": doc_id},
        )

    # 3. Alter column to NOT NULL and change FK (SQLite batch mode)
    with op.batch_alter_table('document', schema=None) as batch_op:
        # Drop the old FK
        batch_op.drop_constraint('fk_document_extractor_id', type_='foreignkey')
        # Alter column to NOT NULL
        batch_op.alter_column('extractor_id', nullable=False)
        # Re-create FK with RESTRICT
        batch_op.create_foreign_key(
            'fk_document_extractor_id',
            'rag_extractor',
            ['extractor_id'],
            ['id'],
            ondelete='RESTRICT',
        )


def downgrade() -> None:
    with op.batch_alter_table('document', schema=None) as batch_op:
        batch_op.drop_constraint('fk_document_extractor_id', type_='foreignkey')
        batch_op.alter_column('extractor_id', nullable=True)
        batch_op.create_foreign_key(
            'fk_document_extractor_id',
            'rag_extractor',
            ['extractor_id'],
            ['id'],
            ondelete='SET NULL',
        )
