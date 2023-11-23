import os
import shutil

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.deps import get_db
from DashAI.back.core.app import create_app
from DashAI.back.core.config import settings

USER_DATASETS_PATH = "DashAI/back/user_datasets"


@pytest.fixture(scope="session")
def app() -> FastAPI:
    settings.DASHAI_TEST_MODE = True
    settings.USER_DATASET_PATH = USER_DATASETS_PATH
    return create_app(settings=settings)


@pytest.fixture(scope="session")
def session():
    from DashAI.back.core import db_session, settings

    if os.path.exists(settings.TEST_DB_PATH):
        os.remove(settings.TEST_DB_PATH)

    return db_session


@pytest.fixture(scope="module", autouse=True)
def _setup_and_delete_db(app: FastAPI, session: sessionmaker):
    try:
        shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv", ignore_errors=True)
        shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv2", ignore_errors=True)
    except OSError:
        pass

    def db():
        try:
            db = session()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db
    yield
    shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv", ignore_errors=True)
    shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv2", ignore_errors=True)


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)
