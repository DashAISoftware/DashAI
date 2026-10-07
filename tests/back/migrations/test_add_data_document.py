import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from DashAI.back.dependencies.database.models import DataDocument


def _config(db_path):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return alembic_cfg


def test_upgrade_creates_and_downgrade_drops_table(tmp_path):
    db_path = tmp_path / "test.db"
    alembic_cfg = _config(db_path)

    command.upgrade(alembic_cfg, "head")
    engine = sa.create_engine(f"sqlite:///{db_path}")
    assert "data_document" in sa.inspect(engine).get_table_names()

    command.downgrade(alembic_cfg, "f4a91c62d8e7")
    assert "data_document" not in sa.inspect(engine).get_table_names()


def test_migration_matches_orm_model(tmp_path):
    db_path = tmp_path / "test.db"
    command.upgrade(_config(db_path), "head")
    engine = sa.create_engine(f"sqlite:///{db_path}")

    columns = sa.inspect(engine).get_columns("data_document")
    migrated = {c["name"]: c["nullable"] for c in columns}
    orm = {c.name: c.nullable for c in DataDocument.__table__.columns}

    assert migrated == orm


def test_rag_document_table_is_untouched(tmp_path):
    db_path = tmp_path / "test.db"
    command.upgrade(_config(db_path), "head")
    engine = sa.create_engine(f"sqlite:///{db_path}")

    columns = {c["name"] for c in sa.inspect(engine).get_columns("document")}
    assert "session_id" in columns
