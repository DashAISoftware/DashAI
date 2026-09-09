import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def test_migration_adds_preprocessing_columns(tmp_path):
    db_path = tmp_path / "test.db"
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(alembic_cfg, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("model_session")}

    assert {
        "preprocessing",
        "input_column_refs",
        "preprocessing_status",
        "preprocessing_error",
        "preprocessing_artifacts_path",
        "preprocessing_job_id",
    } <= columns

    command.downgrade(alembic_cfg, "-1")
    columns_after_downgrade = {
        c["name"] for c in sa.inspect(engine).get_columns("model_session")
    }
    assert "preprocessing" not in columns_after_downgrade
