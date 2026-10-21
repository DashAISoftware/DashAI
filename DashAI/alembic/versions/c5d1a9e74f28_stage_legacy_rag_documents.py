"""stage legacy RAG documents and drop their tables

Copies every legacy ``document`` row, with the extractor it was parsed with,
into ``rag_legacy_document`` and drops ``processed_document_content``,
``document`` and ``rag_extractor``. Every migration runs before any startup
backfill, so the staged rows are what lets ``backfill_rag_documents`` turn the
legacy documents into Data documents on the same startup. The extracted text
cache is not kept: the DataLoader reproduces it from the stored file.

Before the ``document`` table goes, every stored chat citation is made to name
a document of the session that made it, because the backfill remaps citations
session by session. Citations of a deleted document lose their id;
citations that ``k4l5m6n7o8p9`` left on the original of a document it cloned
into several sessions move to the clone of the same file in their session.

This migration performs no filesystem I/O.

Revision ID: c5d1a9e74f28
Revises: b3e8f2c61d47
Create Date: 2026-10-02
"""

import json
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c5d1a9e74f28"
down_revision: Union[str, None] = "b3e8f2c61d47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT_EXTRACTORS = {"pdf": "PypdfExtractor"}
_FALLBACK_EXTRACTOR = "PlainTextExtractor"


def _scope_citations_to_their_session(conn) -> None:
    """Point every chat citation at a legacy document of its own session.

    A citation id that is not a document of the citing session would otherwise
    survive the backfill unchanged and name whichever ``data_document`` later
    takes that id. It moves to the session's document with the same file, or
    becomes None when the session has none.

    Parameters
    ----------
    conn : sqlalchemy.engine.Connection
        Connection of the running migration.
    """
    documents = conn.execute(
        sa.text("SELECT id, session_id, file_hash FROM document")
    ).fetchall()
    session_of = {row.id: row.session_id for row in documents}
    file_of = {row.id: row.file_hash for row in documents}
    by_session_file = {(row.session_id, row.file_hash): row.id for row in documents}
    rows = conn.execute(
        sa.text(
            "SELECT pd.id, pd.data, gp.session_id FROM process_data pd "
            "JOIN generative_process gp ON gp.id = pd.process_id "
            "WHERE pd.data_type = 'Dict'"
        )
    ).fetchall()
    for row in rows:
        try:
            references = json.loads(row.data)
        except (TypeError, ValueError):
            continue
        if not isinstance(references, dict):
            continue
        changed = False
        for reference in references.values():
            if not isinstance(reference, dict):
                continue
            document_id = reference.get("document_id")
            if document_id is None or session_of.get(document_id) == row.session_id:
                continue
            reference["document_id"] = by_session_file.get(
                (row.session_id, file_of.get(document_id))
            )
            changed = True
        if changed:
            conn.execute(
                sa.text("UPDATE process_data SET data = :data WHERE id = :id"),
                {"data": json.dumps(references, ensure_ascii=False), "id": row.id},
            )


def upgrade() -> None:
    _scope_citations_to_their_session(op.get_bind())
    op.create_table(
        "rag_legacy_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_hash", sa.String(), nullable=False),
        sa.Column("optional_metadata", sa.JSON(), nullable=True),
        sa.Column("extractor_component", sa.String(), nullable=True),
        sa.Column("extractor_params", sa.JSON(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_rag_legacy_document"),
    )
    op.execute(
        "INSERT INTO rag_legacy_document (id, session_id, file_name, file_type, "
        "file_path, file_hash, optional_metadata, extractor_component, "
        "extractor_params, created) "
        "SELECT d.id, d.session_id, d.file_name, d.file_type, d.file_path, "
        "d.file_hash, d.optional_metadata, e.component_name, e.params, d.created "
        "FROM document d LEFT JOIN rag_extractor e ON e.id = d.extractor_id"
    )
    op.drop_table("processed_document_content")
    op.drop_table("document")
    op.drop_table("rag_extractor")


def downgrade() -> None:
    """Recreate the legacy tables from the rows still staged.

    Lossy: rows the backfill already converted are Data documents now and are
    not restored, and the extracted text cache comes back empty (the legacy
    code re-extracts on demand).
    """
    op.create_table(
        "rag_extractor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component_name", sa.String(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_rag_extractor"),
    )
    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_hash", sa.String(), nullable=False),
        sa.Column("optional_metadata", sa.JSON(), nullable=True),
        sa.Column("extractor_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["generative_session.id"],
            name="fk_document_session_id_generative_session",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["extractor_id"],
            ["rag_extractor.id"],
            name="fk_document_extractor_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document"),
        sa.UniqueConstraint(
            "session_id", "file_hash", name="uq_document_session_file_hash"
        ),
    )
    op.create_table(
        "processed_document_content",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("signature", sa.String(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name="fk_processed_document_content_document_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processed_document_content"),
        sa.UniqueConstraint(
            "document_id", name="uq_processed_document_content_document"
        ),
    )
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, session_id, file_name, file_type, file_path, file_hash, "
            "optional_metadata, extractor_component, extractor_params, created "
            "FROM rag_legacy_document WHERE session_id IS NOT NULL"
        )
    ).fetchall()
    extractor_ids: dict = {}
    for row in rows:
        component = row.extractor_component or _DEFAULT_EXTRACTORS.get(
            row.file_type, _FALLBACK_EXTRACTOR
        )
        key = (component, row.extractor_params or "{}")
        if key not in extractor_ids:
            conn.execute(
                sa.text(
                    "INSERT INTO rag_extractor (component_name, params) "
                    "VALUES (:component, :params)"
                ),
                {"component": component, "params": key[1]},
            )
            extractor_ids[key] = conn.execute(
                sa.text("SELECT last_insert_rowid()")
            ).scalar()
        conn.execute(
            sa.text(
                "INSERT INTO document (id, session_id, file_name, file_type, "
                "file_path, file_hash, optional_metadata, extractor_id, created, "
                "last_modified) VALUES (:id, :session_id, :file_name, :file_type, "
                ":file_path, :file_hash, :optional_metadata, :extractor_id, "
                "COALESCE(:created, CURRENT_TIMESTAMP), "
                "COALESCE(:created, CURRENT_TIMESTAMP))"
            ),
            {
                "id": row.id,
                "session_id": row.session_id,
                "file_name": row.file_name,
                "file_type": row.file_type,
                "file_path": row.file_path,
                "file_hash": row.file_hash,
                "optional_metadata": row.optional_metadata,
                "extractor_id": extractor_ids[key],
                "created": row.created,
            },
        )
    op.drop_table("rag_legacy_document")
