"""Downgrade of the migration that stores RAG chunks as documents."""

import sqlalchemy as sa
from alembic.config import Config

from alembic import command

PREVIOUS_REVISION = "c5d1a9e74f28"


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


def _chunk_foreign_keys(db_path):
    """Return the named foreign keys of the ``chunk`` table.

    Parameters
    ----------
    db_path : pathlib.Path
        Migrated database file.

    Returns
    -------
    set of str
        Foreign key constraint names.
    """
    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        return {fk["name"] for fk in sa.inspect(engine).get_foreign_keys("chunk")}
    finally:
        engine.dispose()


def test_downgrade_restores_the_chunk_table_constraint_names(tmp_path):
    original = tmp_path / "original.db"
    command.upgrade(_config(original), PREVIOUS_REVISION)

    restored = tmp_path / "restored.db"
    command.upgrade(_config(restored), "head")
    command.downgrade(_config(restored), PREVIOUS_REVISION)

    assert _chunk_foreign_keys(restored) == _chunk_foreign_keys(original)


def test_every_migration_downgrades_to_base(tmp_path):
    db_path = tmp_path / "test.db"
    cfg = _config(db_path)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        tables = set(sa.inspect(engine).get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()
    assert tables == set()
