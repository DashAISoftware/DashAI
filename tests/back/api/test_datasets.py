import os


def test_create_csv_dataset(client):
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
    response = client.post(
        "/api/v1/dataset/",
        data = {"params": '''{  "task_name": "TabularClassificationTask",
                                "dataloader": "CSVDataLoader",
                                "dataset_name": "test_csv2",
                                "class_column": -1,
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
                            }''',
        "url" : ""},
        files={"file": ("filename", csv, "text/csv")}
    )
    assert response.status_code == 201, response.text
    response = client.get("/api/v1/dataset/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_csv"
    assert data["task_name"] == "TabularClassificationTask"
    response = client.get("/api/v1/dataset/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_csv2"

def test_get_all_datasets(client):
    response = client.get("/api/v1/dataset/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_csv"
    assert data[0]["task_name"] == "TabularClassificationTask"
    assert data[1]["name"] == "test_csv2"

def test_get_wrong_dataset(client):
    response = client.get("/api/v1/dataset/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'

def test_modify_dataset(client):
    response = client.patch("/api/v1/dataset/2",
                          params={"name":"test_modify_name",
                                  "task_name":"UnknownTask"})
    assert response.status_code == 200, response.text
    response = client.get("/api/v1/dataset/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_modify_name"
    assert data["task_name"] == "UnknownTask"


def test_delete_dataset(client):
    response = client.delete("/api/v1/dataset/1")
    assert response.status_code == 204, response.text

