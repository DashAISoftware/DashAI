import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DashAI.back.main import api_v1, app
from DashAI.back.database.models import Base
from DashAI.back.api.deps import get_db


@pytest.fixture(scope="session", autouse=True)
def setup_and_delete_db():
    TEST_DB_PATH = "sqlite:///tests/back/test.sqlite"
    engine = create_engine(TEST_DB_PATH)
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
    if os.path.isfile(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
