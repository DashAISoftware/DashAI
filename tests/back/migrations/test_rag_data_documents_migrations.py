"""Upgrade and downgrade of the RAG on Data documents migrations."""

import json

import sqlalchemy as sa
from alembic.config import Config

from alembic import command

PREVIOUS_REVISION = "a4c9d2e7f1b3"
LINK_REVISION = "b3e8f2c61d47"
DOCUMENT_FK_TABLES = ("chunk", "rag_chunk_set_document", "rag_embedding_matrix")


def _config(db_path):
    """Build an Alembic config pointing at a throwaway SQLite file.

    Parameters
    ----------
    db_path : pathlib.Path
        Database file to migrate.

    Returns
    -------
    Config
        Alembic configuration for ``db_path``.
    """
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _document_fk_target(inspector, table):
    """Return the table referenced by ``table.document_id``.

    Parameters
    ----------
    inspector : sqlalchemy.engine.reflection.Inspector
        Inspector bound to the migrated database.
    table : str
        Table holding a ``document_id`` column.

    Returns
    -------
    str or None
        The referenced table name, or None when there is no such key.
    """
    for foreign_key in inspector.get_foreign_keys(table):
        if foreign_key["constrained_columns"] == ["document_id"]:
            return foreign_key["referred_table"]
    return None


def test_link_migration_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "link.db"
    cfg = _config(db_path)
    engine = sa.create_engine(f"sqlite:///{db_path}")

    command.upgrade(cfg, LINK_REVISION)
    inspector = sa.inspect(engine)
    assert "rag_session_document" in inspector.get_table_names()
    uniques = {
        tuple(unique["column_names"])
        for unique in inspector.get_unique_constraints("rag_session_document")
    }
    assert ("session_id", "data_document_id") in uniques
    assert "session_id" in {c["name"] for c in inspector.get_columns("rag_chunk_set")}
    assert "needs_reindex" in {
        c["name"] for c in inspector.get_columns("generative_session")
    }
    for table in DOCUMENT_FK_TABLES:
        assert _document_fk_target(inspector, table) == "data_document"

    command.downgrade(cfg, PREVIOUS_REVISION)
    inspector = sa.inspect(engine)
    assert "rag_session_document" not in inspector.get_table_names()
    assert "session_id" not in {
        c["name"] for c in inspector.get_columns("rag_chunk_set")
    }
    assert "needs_reindex" not in {
        c["name"] for c in inspector.get_columns("generative_session")
    }
    for table in DOCUMENT_FK_TABLES:
        assert _document_fk_target(inspector, table) == "document"
    engine.dispose()


STAGING_REVISION = "c5d1a9e74f28"


def test_staging_migration_keeps_legacy_documents(tmp_path):
    db_path = tmp_path / "staging.db"
    cfg = _config(db_path)
    engine = sa.create_engine(f"sqlite:///{db_path}")
    command.upgrade(cfg, LINK_REVISION)
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO generative_session (id, created, last_modified, "
                "task_name, model_name, parameters, name, needs_reindex) VALUES "
                "(1, '2026-01-01', '2026-01-01', 'RAGTask', 'RAGPipeline', "
                "'{\"documents\": [5]}', 's1', 0)"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO rag_extractor (id, component_name, params) VALUES "
                "(3, 'PdfPlumberExtractor', '{\"layout\": true}')"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO document (id, session_id, file_name, file_type, "
                "file_path, file_hash, optional_metadata, extractor_id, created, "
                "last_modified) VALUES (5, 1, 'a.pdf', 'pdf', '/blobs/h', 'h', "
                "NULL, 3, '2026-01-01', '2026-01-01')"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO processed_document_content (document_id, content, "
                "signature, char_count) VALUES (5, 'text', 'sig', 4)"
            )
        )

    command.upgrade(cfg, STAGING_REVISION)
    tables = set(sa.inspect(engine).get_table_names())
    assert {"document", "processed_document_content", "rag_extractor"}.isdisjoint(
        tables
    )
    with engine.connect() as conn:
        row = conn.execute(
            sa.text(
                "SELECT id, session_id, file_name, file_path, file_hash, "
                "extractor_component, extractor_params FROM rag_legacy_document"
            )
        ).one()
    assert (row.id, row.session_id, row.file_name, row.file_path, row.file_hash) == (
        5,
        1,
        "a.pdf",
        "/blobs/h",
        "h",
    )
    assert row.extractor_component == "PdfPlumberExtractor"
    assert json.loads(row.extractor_params) == {"layout": True}

    command.downgrade(cfg, LINK_REVISION)
    with engine.connect() as conn:
        restored = conn.execute(
            sa.text(
                "SELECT d.id, d.session_id, e.component_name FROM document d "
                "JOIN rag_extractor e ON e.id = d.extractor_id"
            )
        ).one()
    assert tuple(restored) == (5, 1, "PdfPlumberExtractor")
    assert "rag_legacy_document" not in sa.inspect(engine).get_table_names()
    engine.dispose()


def test_staging_migration_scopes_citations_to_their_session(tmp_path):
    db_path = tmp_path / "citations.db"
    cfg = _config(db_path)
    engine = sa.create_engine(f"sqlite:///{db_path}")
    command.upgrade(cfg, LINK_REVISION)
    with engine.begin() as conn:
        for session_id in (1, 2):
            conn.execute(
                sa.text(
                    "INSERT INTO generative_session (id, created, last_modified, "
                    "task_name, model_name, parameters, name, needs_reindex) "
                    "VALUES (:id, '2026-01-01', '2026-01-01', 'RAGTask', "
                    "'RAGPipeline', '{}', :name, 0)"
                ),
                {"id": session_id, "name": f"s{session_id}"},
            )
        conn.execute(
            sa.text(
                "INSERT INTO rag_extractor (id, component_name, params) VALUES "
                "(1, 'PlainTextExtractor', '{}')"
            )
        )
        # Document 5 is the original that k4l5m6n7o8p9 kept in session 1 and
        # 7 its clone in session 2; 8 exists only in session 2.
        for document_id, session_id, file_hash in (
            (5, 1, "h"),
            (7, 2, "h"),
            (8, 2, "k"),
        ):
            conn.execute(
                sa.text(
                    "INSERT INTO document (id, session_id, file_name, file_type, "
                    "file_path, file_hash, optional_metadata, extractor_id, "
                    "created, last_modified) VALUES (:id, :session_id, 'a.txt', "
                    "'txt', '/blobs/x', :file_hash, NULL, 1, '2026-01-01', "
                    "'2026-01-01')"
                ),
                {"id": document_id, "session_id": session_id, "file_hash": file_hash},
            )
        # Document 6 was deleted after it was cited.
        for process_id, session_id, cited in ((1, 1, (5, 6, 8)), (2, 2, (5, 7))):
            conn.execute(
                sa.text(
                    "INSERT INTO generative_process (id, created, last_modified, "
                    "session_id, status) VALUES (:id, '2026-01-01', '2026-01-01', "
                    ":session_id, 'FINISHED')"
                ),
                {"id": process_id, "session_id": session_id},
            )
            references = {
                f"{document_id}_0": {"document_id": document_id, "text": "c"}
                for document_id in cited
            }
            conn.execute(
                sa.text(
                    "INSERT INTO process_data (data, data_type, process_id, "
                    "is_input) VALUES (:data, 'Dict', :process_id, 0)"
                ),
                {"data": json.dumps(references), "process_id": process_id},
            )

    command.upgrade(cfg, STAGING_REVISION)
    with engine.connect() as conn:
        stored = {
            row.process_id: json.loads(row.data)
            for row in conn.execute(
                sa.text("SELECT process_id, data FROM process_data")
            )
        }
    cited = {
        process_id: {key: ref["document_id"] for key, ref in references.items()}
        for process_id, references in stored.items()
    }
    assert cited == {
        1: {"5_0": 5, "6_0": None, "8_0": None},
        2: {"5_0": 7, "7_0": 7},
    }
    engine.dispose()
