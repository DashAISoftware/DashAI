import os
import shutil

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.deps import get_db
from DashAI.back.core.app import create_app
from DashAI.back.core.config import settings
from DashAI.back.database.models import Base

USER_DATASETS_PATH = "DashAI/back/user_datasets"
TEST_DB_PATH = "tests/back/test.sqlite"


@pytest.fixture(scope="session")
def app() -> FastAPI:
    settings.DASHAI_DEV_MODE = True
    return create_app(settings=settings)


@pytest.fixture(scope="session")
def session():
    try:  # noqa: SIM105
        os.remove(TEST_DB_PATH)
    except OSError:
        pass
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
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
