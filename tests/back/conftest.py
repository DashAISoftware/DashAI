import os
import pathlib

import pytest

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
