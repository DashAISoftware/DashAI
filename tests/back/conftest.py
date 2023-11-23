import os
import shutil

import pytest
from fastapi import FastAPI
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

    settings.DB_PATH = "temp/test.sqlite"
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


@pytest.fixture(scope="session")
def client(settings) -> FastAPI:
    from DashAI.back.core.app import create_app

    app = create_app(settings=settings)
    return TestClient(app)


@pytest.fixture(scope="module")
def session(settings):
    from DashAI.back.core import db_session

    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)

    yield db_session

    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
