import pathlib
import shutil

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

TEST_PATH = "tmp"


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app(local_path=pathlib.Path(TEST_PATH), logging_level="DEBUG")

    yield TestClient(app)

    app.container.db().dispose_engine()
    shutil.rmtree(app.container.config.provided()["LOCAL_PATH"])
