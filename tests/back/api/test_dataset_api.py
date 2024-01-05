import os

from fastapi.testclient import TestClient


def test_create_csv_dataset(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "dataset_name": "test_csv",
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
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "dataset_name": "test_csv2",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3,
                                        "seed": 42,
                                        "shuffle": true,
                                        "stratify": false
                                    },
                                    "dataloader_params": {
                                        "separator": ","
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    assert response.status_code == 201, response.text
    response = client.get("/api/v1/dataset/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_csv"
    response = client.get("/api/v1/dataset/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_csv2"


def test_get_all_datasets(client: TestClient):
    response = client.get("/api/v1/dataset/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_csv"
    assert data[1]["name"] == "test_csv2"


def test_get_wrong_dataset(client: TestClient):
    response = client.get("/api/v1/dataset/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'


def test_get_types(client: TestClient):
    response = client.get("/api/v1/dataset/types/2")
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
