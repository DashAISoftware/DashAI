"""Dataloaders tests."""
import io
import shutil

import pytest
from datasets import DatasetDict
from datasets.builder import DatasetGenerationError
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader


def test_csv_dataloader_to_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    test_dataloader = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    dataset = test_dataloader.load_data(
        file=file,
        temp_path="tests/back/dataloaders",
        params=params,
    )
    assert isinstance(dataset, DatasetDict)


def test_json_dataloader_to_dataset():
    test_dataset_path = "tests/back/dataloaders/irisDataset.json"
    test_dataloader = JSONDataLoader()
    params = {"data_key": "data"}

    with open(test_dataset_path, "r") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    dataset = test_dataloader.load_data(
        file=file,
        temp_path="tests/back/dataloaders",
        params=params,
    )
    assert isinstance(dataset, DatasetDict)


def test_wrong_create_csv_dataloader():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    test_dataloader = CSVDataLoader()
    params = {"any_param": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    with pytest.raises(
        ValueError,
        match=r"Error loading CSV file: separator parameter was not provided.",
    ):
        test_dataloader.load_data(
            file=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )


def test_wrong_create_json_dataloader():
    test_dataset_path = "tests/back/dataloaders/irisDataset.json"
    test_dataloader = JSONDataLoader()
    params = {"data_ke": "data"}
    with open(test_dataset_path, "r") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    with pytest.raises(
        ValueError,
        match=r"Error loading JSON file: data_key parameter was not provided.",
    ):
        test_dataloader.load_data(
            file=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )


def test_invalidate_csv_dataloader():
    test_dataset_path = "tests/back/dataloaders/wrong_iris.csv"
    test_dataloader = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    with pytest.raises(DatasetGenerationError):
        test_dataloader.load_data(
            file=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )


def test_csv_dataloader_from_zip():
    test_dataset_path = "tests/back/dataloaders/iris_csv.zip"
    test_dataloader = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "rb") as file:
        upload_file = UploadFile(
            filename=test_dataset_path,
            file=file,
            headers=Headers({"Content-Type": "application/zip"}),
        )

        dataset = test_dataloader.load_data(
            file=upload_file,
            temp_path="tests/back/dataloaders/iris",
            params=params,
        )

    assert isinstance(dataset, DatasetDict)


def test_image_dataloader_from_zip():
    test_dataset_path = "tests/back/dataloaders/beans_dataset_small.zip"
    test_dataloader = ImageDataLoader()

    with open(test_dataset_path, "rb") as file:
        uploaded_file = UploadFile(
            filename=test_dataset_path,
            file=file,
            headers=Headers({"Content-Type": "application/zip"}),
        )

        dataset = test_dataloader.load_data(
            file=uploaded_file,
            temp_path="tests/back/dataloaders/beans_dataset_small",
            params={},
        )

    assert isinstance(dataset, DatasetDict)

    shutil.rmtree("tests/back/dataloaders/beans_dataset_small", ignore_errors=True)
