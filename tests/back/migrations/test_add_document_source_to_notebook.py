"""Upgrade and downgrade test for the document source on notebooks."""

from datetime import datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

REVISION = "a4c9d2e7f1b3"
CHECK_NAME = "ck_notebook_exactly_one_source"
NOW = datetime(2026, 10, 7, 12, 0, 0)


def _alembic_config(db_path) -> Config:
    """Build an Alembic config for a temporary SQLite file.

    Parameters
    ----------
    db_path : pathlib.Path
        Path of the SQLite file.

    Returns
    -------
    Config
        Config pointing at ``db_path``.
    """
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _seed_sources(engine: sa.Engine) -> None:
    """Insert a dataset, a finished document and one dataset notebook.

    Parameters
    ----------
    engine : sa.Engine
        Engine bound to the database at the pre-upgrade revision.
    """
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO dataset (id, name, file_path, status, created, "
                "last_modified) VALUES (1, 'iris', '/tmp/iris', 'FINISHED', "
                ":now, :now)"
            ),
            {"now": NOW},
        )
        conn.execute(
            sa.text(
                "INSERT INTO data_document (id, name, file_name, file_type, "
                "file_hash, file_path, dataloader, dataloader_params, "
                "content_counts, total_pages, status, created, last_modified) "
                "VALUES (1, 'paper', 'paper.pdf', 'pdf', :hash, '/tmp/paper', "
                "'PypdfDocumentDataLoader', :params, :counts, 1, 'FINISHED', "
                ":now, :now)"
            ),
            {"now": NOW, "hash": "0" * 64, "params": "{}", "counts": '{"Text": 1}'},
        )
        conn.execute(
            sa.text(
                "INSERT INTO notebook (id, dataset_id, file_path, created, "
                "last_modified) VALUES (1, 1, '/tmp/nb1', :now, :now)"
            ),
            {"now": NOW},
        )


def _foreign_keys(engine: sa.Engine) -> dict:
    """Return the notebook foreign keys keyed by referred table.

    Parameters
    ----------
    engine : sa.Engine
        Engine bound to the database.

    Returns
    -------
    dict
        Referred table name to the reflected foreign key.
    """
    return {
        fk["referred_table"]: fk
        for fk in sa.inspect(engine).get_foreign_keys("notebook")
    }


def test_document_source_migration_round_trip(tmp_path):
    db_path = tmp_path / "test.db"
    cfg = _alembic_config(db_path)
    down_revision = (
        ScriptDirectory.from_config(cfg).get_revision(REVISION).down_revision
    )
    command.upgrade(cfg, down_revision)
    engine = sa.create_engine(f"sqlite:///{db_path}")
    _seed_sources(engine)

    command.upgrade(cfg, REVISION)

    inspector = sa.inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("notebook")}
    assert columns["dataset_id"]["nullable"] is True
    assert columns["document_id"]["nullable"] is True
    foreign_keys = _foreign_keys(engine)
    assert foreign_keys["data_document"]["constrained_columns"] == ["document_id"]
    assert foreign_keys["data_document"]["options"].get("ondelete") == "CASCADE"
    assert foreign_keys["dataset"]["options"].get("ondelete") == "CASCADE"
    checks = {c["name"] for c in inspector.get_check_constraints("notebook")}
    assert CHECK_NAME in checks

    with engine.begin() as conn:
        kept = conn.execute(
            sa.text("SELECT dataset_id FROM notebook WHERE id = 1")
        ).scalar_one()
        assert kept == 1
        conn.execute(
            sa.text(
                "INSERT INTO notebook (id, document_id, file_path, created, "
                "last_modified) VALUES (2, 1, '/tmp/nb2', :now, :now)"
            ),
            {"now": NOW},
        )
        conn.execute(
            sa.text(
                "INSERT INTO converter (notebook_id, converter, parameters, "
                "status, created, last_modified) VALUES (2, 'Noop', '{}', "
                "'NOT_STARTED', :now, :now)"
            ),
            {"now": NOW},
        )
        conn.execute(
            sa.text(
                "INSERT INTO explorer (notebook_id, columns, exploration_type, "
                "parameters, status, created, last_modified) VALUES (2, '[]', "
                "'DescribeExplorer', '{}', 'NOT_STARTED', :now, :now)"
            ),
            {"now": NOW},
        )

    with pytest.raises(sa.exc.IntegrityError), engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO notebook (id, file_path, created, last_modified) "
                "VALUES (3, '/tmp/nb3', :now, :now)"
            ),
            {"now": NOW},
        )
    with pytest.raises(sa.exc.IntegrityError), engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO notebook (id, dataset_id, document_id, file_path, "
                "created, last_modified) VALUES (4, 1, 1, '/tmp/nb4', :now, :now)"
            ),
            {"now": NOW},
        )

    command.downgrade(cfg, down_revision)

    inspector = sa.inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("notebook")}
    assert "document_id" not in columns
    assert columns["dataset_id"]["nullable"] is False
    assert _foreign_keys(engine)["dataset"]["options"].get("ondelete") == "CASCADE"
    assert inspector.get_check_constraints("notebook") == []
    with engine.connect() as conn:
        remaining = conn.execute(sa.text("SELECT id FROM notebook")).scalars().all()
        converters = conn.execute(
            sa.text("SELECT COUNT(*) FROM converter")
        ).scalar_one()
        explorers = conn.execute(sa.text("SELECT COUNT(*) FROM explorer")).scalar_one()
    assert remaining == [1]
    assert converters == 0
    assert explorers == 0
    engine.dispose()
