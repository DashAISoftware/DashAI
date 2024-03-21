import pathlib
import shutil
import time
import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

TEST_PATH = "tmp"

def remove_dir_with_retry(directory, max_attempts=5, sleep_seconds=1):
    for attempt in range(max_attempts):
        try:
            shutil.rmtree(directory)
            print(f"Successfully removed directory: {directory}")
            break
        except PermissionError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(sleep_seconds)
    else:
        print(f"Failed to remove directory after {max_attempts} attempts.")

@pytest.fixture(scope="module", autouse=True)
def client():
    app = create_app(local_path=pathlib.Path(TEST_PATH), logging_level="ERROR")

    yield TestClient(app)

    app.container.db().dispose_engine()
    remove_dir_with_retry(app.container.config.provided()["LOCAL_PATH"])
