"""scope RAG documents to a single session

Gives ``document`` a ``session_id`` foreign key, so a document belongs to
exactly one RAG session instead of being a globally deduplicated library
entry. ``UNIQUE(file_hash)`` becomes ``UNIQUE(session_id, file_hash)``: the
same file uploaded into two sessions is now two rows, each free to pick its
own extractor without disturbing the other.

Also drops ``rag_document_pipeline_session_link``, which nothing in
production ever wrote to.

This migration performs **no filesystem I/O**. Existing rows keep their
current ``file_path``, and cloned rows deliberately share the path of the
original; only uploads made after this migration use the content-addressed
``blobs/`` layout. Deletion is reference-counted by ``file_path``, so a shared
path is only unlinked once the last row pointing at it is gone.

Revision ID: k4l5m6n7o8p9
Revises: b7c1d4e9f206
Create Date: 2026-09-03
"""

import json
import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k4l5m6n7o8p9"
down_revision: Union[str, None] = "b7c1d4e9f206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")

#: Tables holding rows that reference a document, in deletion order.
_DEPENDENT_TABLES = (
    "chunk",
    "rag_embedding_matrix",
    "rag_chunk_set_document",
    "processed_document_content",
    "rag_document_pipeline_session_link",
)


def _load_parameters(raw) -> dict:
    """Return a session's ``parameters`` as a dict, whatever the driver gave us."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _document_owners(conn) -> dict:
    """Map each document id to the RAG sessions claiming it, lowest id first.

    The pre-migration link between a document and a session is the JSON list
    ``generative_session.parameters["documents"]``.
    """
    owners: dict = {}
    rows = conn.execute(
        sa.text(
            "SELECT id, parameters FROM generative_session "
            "WHERE task_name = 'RAGTask' ORDER BY id"
        )
    ).fetchall()
    for session_id, raw in rows:
        for doc_id in _load_parameters(raw).get("documents") or []:
            if isinstance(doc_id, bool) or not isinstance(doc_id, int):
                continue
            owners.setdefault(doc_id, []).append(session_id)
    return owners


def _delete_documents(conn, doc_ids) -> None:
    """Delete documents and every row referencing them."""
    if not doc_ids:
        return
    present = set(sa.inspect(conn).get_table_names())
    for doc_id in doc_ids:
        for table in _DEPENDENT_TABLES:
            if table in present:
                conn.execute(
                    sa.text("DELETE FROM " + table + " WHERE document_id = :did"),
                    {"did": doc_id},
                )
        conn.execute(sa.text("DELETE FROM document WHERE id = :did"), {"did": doc_id})


def _clone_document(conn, doc_id: int, session_id: int) -> int:
    """Copy a document row (and its cached text) over to another session.

    The clone reuses the original's ``extractor_id`` -- ``rag_extractor`` rows
    are immutable value objects -- and its ``file_path``, since the bytes on
    disk are identical. Chunks, embeddings and chunk-set membership are
    deliberately *not* copied: changing a session's document list changes its
    chunk-set signature, so the session re-indexes by itself on its next
    message.
    """
    conn.execute(
        sa.text(
            "INSERT INTO document (session_id, file_name, file_type, file_path, "
            "file_hash, optional_metadata, extractor_id, created, last_modified) "
            "SELECT :sid, file_name, file_type, file_path, file_hash, "
            "optional_metadata, extractor_id, created, last_modified "
            "FROM document WHERE id = :did"
        ),
        {"sid": session_id, "did": doc_id},
    )
    new_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
    conn.execute(
        sa.text(
            "INSERT INTO processed_document_content "
            "(document_id, content, signature, char_count) "
            "SELECT :new_id, content, signature, char_count "
            "FROM processed_document_content WHERE document_id = :did"
        ),
        {"new_id": new_id, "did": doc_id},
    )
    return new_id


def _replace_in_session_documents(
    conn, session_id: int, old_id: int, new_id: int
) -> None:
    """Point a session's ``documents`` list at its own clone."""
    raw = conn.execute(
        sa.text("SELECT parameters FROM generative_session WHERE id = :sid"),
        {"sid": session_id},
    ).scalar()
    parameters = _load_parameters(raw)
    parameters["documents"] = [
        new_id if doc_id == old_id else doc_id
        for doc_id in parameters.get("documents") or []
    ]
    conn.execute(
        sa.text("UPDATE generative_session SET parameters = :params WHERE id = :sid"),
        {"params": json.dumps(parameters), "sid": session_id},
    )


def upgrade() -> None:
    conn = op.get_bind()

    # The global UNIQUE(file_hash) has to go before the backfill, not after:
    # splitting a shared document into one row per session inserts rows that
    # deliberately repeat a hash.
    with op.batch_alter_table("document", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.Integer(), nullable=True))
        batch_op.drop_constraint("uq_document_file_hash", type_="unique")

    owners = _document_owners(conn)
    all_doc_ids = {
        row[0] for row in conn.execute(sa.text("SELECT id FROM document")).fetchall()
    }

    # Orphans: with the global documents page gone these are unreachable
    # forever, and a nullable session_id would defeat the whole invariant.
    orphans = sorted(doc_id for doc_id in all_doc_ids if doc_id not in owners)
    if orphans:
        abandoned = conn.execute(
            sa.text("SELECT id, file_path FROM document WHERE session_id IS NULL")
        ).fetchall()
        log.info(
            "Deleting %d RAG document(s) that no session references. Their files "
            "are left on disk for manual cleanup: %s",
            len(orphans),
            ", ".join(
                "#%s %s" % (doc_id, path)
                for doc_id, path in abandoned
                if doc_id in set(orphans)
            ),
        )
        _delete_documents(conn, orphans)

    for doc_id, session_ids in sorted(owners.items()):
        if doc_id not in all_doc_ids:
            continue  # stale id left behind in a session's parameters
        conn.execute(
            sa.text("UPDATE document SET session_id = :sid WHERE id = :did"),
            {"sid": session_ids[0], "did": doc_id},
        )
        for extra_session_id in session_ids[1:]:
            new_id = _clone_document(conn, doc_id, extra_session_id)
            _replace_in_session_documents(conn, extra_session_id, doc_id, new_id)

    # Anything still unclaimed (e.g. a document whose session was deleted
    # without its parameters being cleaned up) has nothing left to belong to.
    _delete_documents(
        conn,
        [
            row[0]
            for row in conn.execute(
                sa.text("SELECT id FROM document WHERE session_id IS NULL")
            ).fetchall()
        ],
    )

    # upload() wrote params={} while update_extractor() wrote NULL, which is one
    # reason extractor rows could never be deduplicated. Settle on {}.
    conn.execute(sa.text("UPDATE rag_extractor SET params = '{}' WHERE params IS NULL"))

    with op.batch_alter_table("document", schema=None) as batch_op:
        batch_op.alter_column("session_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_document_session_id_generative_session",
            "generative_session",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "uq_document_session_file_hash", ["session_id", "file_hash"]
        )

    if "rag_document_pipeline_session_link" in sa.inspect(conn).get_table_names():
        op.drop_table("rag_document_pipeline_session_link")


def downgrade() -> None:
    """Restore the global document library.

    Lossy: ``UNIQUE(file_hash)`` cannot be restored while per-session copies of
    the same file exist, so every copy but the lowest-id one is deleted.
    ``rag_document_pipeline_session_link`` comes back empty, which is the only
    state it was ever in.
    """
    conn = op.get_bind()

    duplicates = [
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT id FROM document WHERE id NOT IN "
                "(SELECT MIN(id) FROM document GROUP BY file_hash)"
            )
        ).fetchall()
    ]
    _delete_documents(conn, duplicates)

    with op.batch_alter_table("document", schema=None) as batch_op:
        batch_op.drop_constraint("uq_document_session_file_hash", type_="unique")
        batch_op.drop_constraint(
            "fk_document_session_id_generative_session", type_="foreignkey"
        )
        batch_op.drop_column("session_id")
        batch_op.create_unique_constraint("uq_document_file_hash", ["file_hash"])

    op.create_table(
        "rag_document_pipeline_session_link",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["generative_session.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_id"], ["rag_pipeline.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "session_id", name="uix_document_session"),
        sa.UniqueConstraint("session_id", "pipeline_id", name="uix_session_pipeline"),
        sa.UniqueConstraint("document_id", "pipeline_id", name="uix_document_pipeline"),
    )
