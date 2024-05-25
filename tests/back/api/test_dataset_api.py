import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(name="response_1", autouse=True)
def create_dataset_1(client):
    """Create testing dataset 1."""
    abs_file_path = os.path.join(os.path.dirname(__file__), "iris.csv")

    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "name": "test_csv",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.8,
                                        "test_size": 0.1,
                                        "val_size": 0.1
                                    },
                                    "separator": ",",
                                    "more_options": {
                                        "seed": 42,
                                        "shuffle": true,
                                        "stratify": false
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    return response


@pytest.fixture(name="response_2", autouse=True)
def create_dataset_2(client):
    """Create testing dataset 2."""
    abs_file_path = os.path.join(os.path.dirname(__file__), "iris.csv")

    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "name": "test_csv2",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3
                                    },
                                    "separator": ",",
                                    "more_options": {
                                        "seed": 42,
                                        "shuffle": true,
                                        "stratify": false
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )

    return response


def test_create_csv_dataset(client: TestClient, response_1, response_2) -> None:
    assert response_1.status_code == 201, response_1.text
    response_1 = client.get("/api/v1/dataset/1")
    assert response_1.status_code == 200, response_1.text
    data = response_1.json()
    assert data["name"] == "test_csv"
    response_2 = client.get("/api/v1/dataset/2")
    assert response_2.status_code == 200, response_2.text
    data = response_2.json()
    assert data["name"] == "test_csv2"


def test_get_all_datasets(client: TestClient):
    response = client.get("/api/v1/dataset/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_csv"
    assert data[1]["name"] == "test_csv2"


def test_get_unexistant_dataset(client: TestClient):
    response = client.get("/api/v1/dataset/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'


def test_get_types(client: TestClient):
    response = client.get("/api/v1/dataset/2/types")
    data = response.json()
    assert data == {
        "SepalLengthCm": {"type": "Value", "dtype": "float64"},
        "SepalWidthCm": {"type": "Value", "dtype": "float64"},
        "PetalLengthCm": {"type": "Value", "dtype": "float64"},
        "PetalWidthCm": {"type": "Value", "dtype": "float64"},
        "Species": {"type": "Value", "dtype": "string"},
    }


def test_modify_dataset_name(client: TestClient):
    response = client.patch(
        "/api/v1/dataset/2",
        json={"name": "test_modify_name"},
    )
    assert response.status_code == 200, response.text
    response = client.get("/api/v1/dataset/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_modify_name"


def test_delete_dataset(client: TestClient):
    response = client.delete("/api/v1/dataset/1")
    assert response.status_code == 204, response.text

    response = client.delete("/api/v1/dataset/2")
    assert response.status_code == 204, response.text
