"""Upgrade and downgrade of the RAG on Data documents migrations."""

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

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
