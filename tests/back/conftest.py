import os
import pathlib
import shutil
import time

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

TEST_PATH = pathlib.Path("tmp")
TEST_DATASETS_PATH = pathlib.Path("./tests/back/test_datasets")
RANDOM_STATE = 50


@pytest.fixture(scope="session", autouse=True)
def test_path():
    return TEST_PATH


@pytest.fixture(scope="session", autouse=True)
def random_state():
    return RANDOM_STATE


@pytest.fixture(scope="session", autouse=True)
def test_datasets_path():
    os.makedirs(TEST_DATASETS_PATH, exist_ok=True)

    # .gitignore
    with open(TEST_DATASETS_PATH / ".gitignore", "w") as f:
        f.write("*")

    return TEST_DATASETS_PATH


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

    app.container["engine"].dispose()
    remove_dir_with_retry(app.container["config"]["LOCAL_PATH"])
