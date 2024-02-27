import shutil
import time

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

TEST_PATH = "tmp"


@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app()

    yield TestClient(app)
    time.sleep(10)
    shutil.rmtree(app.container.config.provided()["LOCAL_PATH"])
