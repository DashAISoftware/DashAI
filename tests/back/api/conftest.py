import pathlib
import shutil

import pytest
from fastapi.testclient import TestClient

from DashAI.back.database.database import SQLiteDatabase
from DashAI.back.server import _create_path, create_app

TEST_PATH = "tmp"
TEST_DATASETS_PATH = "tmp/datasets"
TEST_RUNS_PATH = "tmp/runs"
TEST_SQLITE_DB_PATH = "tmp/test_db.sqlite"


@pytest.fixture(scope="module")
def client():
    app = create_app()

    with app.container.db.override(SQLiteDatabase, db_path=TEST_SQLITE_DB_PATH):
        _create_path(TEST_DATASETS_PATH)
        _create_path(TEST_RUNS_PATH)

        db = app.container.db.provided()
        db.create_database()

        yield TestClient(app)

    shutil.rmtree(pathlib.Path(TEST_PATH).expanduser())
