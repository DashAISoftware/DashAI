import os
import shutil

import pytest
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings


@pytest.fixture(scope="session")
def _create_temp_path():
    shutil.rmtree("temp", ignore_errors=True)
    os.makedirs("temp", exist_ok=True)

    yield
    shutil.rmtree("temp", ignore_errors=True)


@pytest.fixture(scope="session")
def settings(_create_temp_path) -> BaseSettings:
    from DashAI.back.config import settings

    settings.DASHAI_TEST_MODE = True

    settings.DB_URL = "temp/test.sqlite"
    settings.DATASETS_PATH = "temp/user_datasets"
    settings.RUNS_PATH = "temp/user_runs"

    return settings


@pytest.fixture(scope="module", autouse=True)
def _delete_test_files(settings):
    shutil.rmtree(settings.DATASETS_PATH, ignore_errors=True)
    shutil.rmtree(settings.RUNS_PATH, ignore_errors=True)

    os.makedirs(settings.DATASETS_PATH)
    os.makedirs(settings.RUNS_PATH)

    yield

    shutil.rmtree(settings.DATASETS_PATH, ignore_errors=True)
    shutil.rmtree(settings.RUNS_PATH, ignore_errors=True)


@pytest.fixture(scope="module")
def client(settings):
    from DashAI.back.core.app import create_app

    app = create_app(settings=settings)
    client = TestClient(app)
    return client


@pytest.fixture(scope="module")
def session(settings):
    from DashAI.back.dependencies import db_session

    return db_session
