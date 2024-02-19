import shutil

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

TEST_PATH = "tmp"


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app(TEST_PATH)

    yield TestClient(app)

    shutil.rmtree(app.container.config.provided()["LOCAL_PATH"])
