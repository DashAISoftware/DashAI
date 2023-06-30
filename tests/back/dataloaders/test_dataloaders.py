import io

import pytest
from datasets import DatasetDict
from datasets.builder import DatasetGenerationError
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader


def test_csv_dataloader_to_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert isinstance(dataset, DatasetDict)


def test_json_dataloader_to_dataset():
    test_dataset_path = "tests/back/dataloaders/irisDataset.json"
    dataloader_test = JSONDataLoader()
    params = {"data_key": "data"}

    with open(test_dataset_path, "r") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert isinstance(dataset, DatasetDict)


def test_wrong_create_csv_dataloader():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separato": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    with pytest.raises(
        ValueError,
        match=r"Error loading CSV file: separator parameter was not provided.",
    ):
        dataloader_test.load_data("tests/back/dataloaders", params, file=file)


def test_wrong_create_json_dataloader():
    test_dataset_path = "tests/back/dataloaders/irisDataset.json"
    dataloader_test = JSONDataLoader()
    params = {"data_ke": "data"}
    with open(test_dataset_path, "r") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    with pytest.raises(
        ValueError,
        match=r"Error loading JSON file: data_key parameter was not provided.",
    ):
        dataloader_test.load_data("tests/back/dataloaders", params, file=file)


def test_wrong_path_create_json_dataloader():
    test_dataset_path = "tests/back/dataloaders/irisDatasetUnexisted.json"
    dataloader_test = JSONDataLoader()  # noqa: F841
    params = {"data_key": "data"}  # noqa: F841
    with pytest.raises(FileNotFoundError), open(test_dataset_path, "r") as file:
        json_data = file.read()  # noqa: F841


def test_invalidate_csv_dataloader():
    test_dataset_path = "tests/back/dataloaders/wrong_iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    with pytest.raises(DatasetGenerationError):
        dataloader_test.load_data("tests/back/dataloaders", params, file=file)
