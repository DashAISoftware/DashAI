"""Tabular Dataloaders tests."""

import io
from typing import Any, Dict, Type

import pytest
from datasets import DatasetDict
from datasets.builder import DatasetGenerationError
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders import BaseDataLoader, CSVDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader

IRIS_CSV_PATH = "tests/back/dataloaders/iris.csv"
IRIS_JSON_PATH = "tests/back/dataloaders/irisDataset.json"
IRIS_CSV_ZIP_PATH = "tests/back/dataloaders/iris_csv.zip"
IRIS_CSV_INVALID_PATH = "tests/back/dataloaders/wrong_iris.csv"


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params"),
    [
        (CSVDataLoader, IRIS_CSV_PATH, {"separator": ","}),
        (JSONDataLoader, IRIS_JSON_PATH, {"data_key": "data"}),
    ],
)
def test_dataloader_from_file(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
) -> None:
    """
    Tests the `load_data` method of a `BaseDataLoader` subclass by loading data from
    different file formats and verifying the loaded dataset structure.

    Parameters
    ----------
    dataloader_cls : Type[BaseDataLoader]
        The class of the `BaseDataLoader` subclass to test.
    dataset_path : str
        The path to the dataset file.
    params : Dict[str, Any]
        Additional parameters to pass to the `load_data` method.
    """
    # instance the dataloader
    dataloder_instance = dataloader_cls()

    # open the dataset
    with open(dataset_path, "r") as file:
        loaded_bytes = file.read()
        bytes_buffer = io.BytesIO(bytes(loaded_bytes, encoding="utf8"))
        file = UploadFile(bytes_buffer)

    # load data
    dataset = dataloder_instance.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params=params,
    )

    # check if the dataset is a dataset dict and its correctly loaded.
    assert isinstance(dataset, DatasetDict)
    assert "train" in dataset
    assert dataset["train"].num_rows > 0
    assert dataset["train"].num_columns > 0


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params"),
    [
        (CSVDataLoader, IRIS_CSV_ZIP_PATH, {"separator": ","}),
        # (JSONDataLoader, IRIS_JSON_PATH, {"data_key": "data"}),  # noqa: ERA001
    ],
)
def test_dataloader_from_zip(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
) -> None:
    """
    Tests the `load_data` method of a `BaseDataLoader` subclass by loading data from a
    zipped file and verifying that the loaded files structure (train, test and
    validation paths with each own files) is correct.

    Parameters
    ----------
    dataloader_cls : Type[BaseDataLoader]
        The class of the `BaseDataLoader` subclass to test.
    dataset_path : str
        The path to the zipped dataset file.
    params : Dict[str, Any]
        Additional parameters to pass to the `load_data` method.
    """

    # instance the dataloader
    dataloder_instance = dataloader_cls()

    # open the dataset
    with open(dataset_path, "rb") as file:
        upload_file = UploadFile(
            filename=dataset_path,
            file=file,
            headers=Headers({"Content-Type": "application/zip"}),
        )

        dataset = dataloder_instance.load_data(
            filepath_or_buffer=upload_file,
            temp_path="tests/back/dataloaders/iris",
            params=params,
        )

    # check each dataset of the datasetdict.
    assert isinstance(dataset, DatasetDict)

    assert "train" in dataset
    assert dataset["train"].num_rows > 0
    assert dataset["train"].num_columns > 0

    assert "test" in dataset
    assert dataset["test"].num_rows > 0
    assert dataset["test"].num_columns > 0

    assert "validation" in dataset
    assert dataset["validation"].num_rows > 0
    assert dataset["validation"].num_columns > 0


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params", "expected_error_msg"),
    [
        (
            CSVDataLoader,
            IRIS_CSV_PATH,
            {"not_a_valid_param": ","},
            r"Error loading CSV file: separator parameter was not provided.",
        ),
        (
            JSONDataLoader,
            IRIS_JSON_PATH,
            {"not_a_valid_param": "data"},
            r"Error loading JSON file: data_key parameter was not provided.",
        ),
    ],
)
def test_dataloader_missing_required_params(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
    expected_error_msg: str,
) -> None:
    """
    Tests the `load_data` method of a `BaseDataLoader` subclass by providing invalid
    parameters and verifying that the expected error message is raised.

    Parameters
    ----------
    dataloader_cls : Type[BaseDataLoader]
        The class of the `BaseDataLoader` subclass to test.
    dataset_path : str
        The path to the dataset file.
    params : Dict[str, Any]
        Invalid parameters to pass to the `load_data` method.
    expected_error_msg : str
        The expected error message to be raised.

    """

    # instance the dataloader
    dataloder_instance = dataloader_cls()

    # open the dataset
    with open(dataset_path, "r") as file:
        loaded_bytes = file.read()
        bytes_buffer = io.BytesIO(bytes(loaded_bytes, encoding="utf8"))
        file = UploadFile(bytes_buffer)

    # try to load the dataloader with the wrong params, catch the exception and
    # compare the exception msg with the expected one.
    with pytest.raises(
        ValueError,
        match=expected_error_msg,
    ):
        dataloder_instance.load_data(
            filepath_or_buffer=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params"),
    [
        (CSVDataLoader, IRIS_CSV_INVALID_PATH, {"separator": ","}),
    ],
)
def test_dataloader_try_to_load_a_invalid_datasets(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
) -> None:
    """
    Tests the `load_data` method of a `BaseDataLoader` subclass by loading data
    from an invalid dataset path and verifying that the expected error is raised.

    Parameters
    ----------
    dataloader_cls : Type[BaseDataLoader]
        The class of the `BaseDataLoader` subclass to test.
    dataset_path : str
        The path to the invalid dataset file.
    params : Dict[str, Any]
        Additional parameters to pass to the `load_data` method.
    """

    # instance the dataloader
    dataloder_instance = dataloader_cls()

    # open the dataset
    with open(dataset_path, "r") as file:
        loaded_bytes = file.read()
        bytes_buffer = io.BytesIO(bytes(loaded_bytes, encoding="utf8"))
        file = UploadFile(bytes_buffer)

    # try to load the dataloader with the wrong params, catch the exception and
    # compare the exception msg with the expected one.
    with pytest.raises(
        DatasetGenerationError,
    ):
        dataloder_instance.load_data(
            filepath_or_buffer=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )
