from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DashAI.back.main import api_v1, app
from DashAI.back.database.models import Base
from DashAI.back.api.deps import get_db
import os
from DashAI.back.core.config import settings

SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.TEST_DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


api_v1.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_csv_dataset():
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    csv = open(abs_file_path, 'rb')
    response = client.post(
        "/api/v1/dataset/",
        data = {"params": '''{  "task_name": "TabularClassificationTask",
                                "dataloader": "CSVDataLoader",
                                "dataset_name": "test_csv",
                                "class_column": -1,
                                "splits_in_folders": false,
                                "splits": {
                                    "train_size": 0.8,
                                    "test_size": 0.1,
                                    "val_size": 0.1,
                                    "seed": 42,
                                    "shuffle": true,
                                    "stratify": false
                                },
                                "dataloader_params": {
                                    "separator": ","
                                }
                            }''',
        "url" : ""},
        files={"file": ("filename", csv, "text/csv")}
    )
    assert response.status_code == 200, response.text
