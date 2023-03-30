import os
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DashAI.back.main import api_v1, app
from DashAI.back.database.models import Base
from DashAI.back.api.deps import get_db

USER_DATASETS_PATH = "DashAI/back/user_datasets"
TEST_DB_PATH = "tests/back/test.sqlite"

@pytest.fixture(scope="session", autouse=True)
def setup_and_delete_db():
    try:
        shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv", ignore_errors=True)
        shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv2", ignore_errors=True)
        os.remove(TEST_DB_PATH)
    except OSError:
        pass
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    def db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    api_v1.dependency_overrides[get_db] = db
    yield
    shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv", ignore_errors=True)
    shutil.rmtree(f"{USER_DATASETS_PATH}/test_csv2", ignore_errors=True)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
