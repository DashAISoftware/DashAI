"""Tabular Dataloaders tests."""

import io
import os
import pathlib
from typing import Any, Dict, Type

import pytest
from datasets import DatasetDict
from datasets.builder import DatasetGenerationError
from fastapi.datastructures import Headers
from sklearn.datasets import load_diabetes, load_iris, load_wine
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders import BaseDataLoader, CSVDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from tests.back.test_datasets_generator import (
    CSVTestDatasetGenerator,
    JSONTestDatasetGenerator,
)

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")
CSV_IRIS_PATH = TEST_DATASETS_PATH / "csv" / "iris"
CSV_WINE_PATH = TEST_DATASETS_PATH / "csv" / "wine"
CSV_DIABETES_PATH = TEST_DATASETS_PATH / "csv" / "diabetes"
JSON_IRIS_PATH = TEST_DATASETS_PATH / "json" / "iris"


# TODO: Test no header, empty file, bad split folder structure.


@pytest.fixture(scope="module", autouse=True)
def _generate_test_datasets() -> None:
    TEST_DATASETS_PATH = pathlib.Path("./tests/back/test_datasets")
    RANDOM_STATE = 50
    os.makedirs(TEST_DATASETS_PATH, exist_ok=True)

    # .gitignore
    with open(TEST_DATASETS_PATH / ".gitignore", "w") as f:
        f.write("*")

    # generate tests datasets
    df_iris = load_iris(return_X_y=False, as_frame=True)["frame"]  # type: ignore
    CSVTestDatasetGenerator(
        df=df_iris,
        dataset_name="iris",
        ouptut_path=TEST_DATASETS_PATH,
        random_state=RANDOM_STATE,
    )
    JSONTestDatasetGenerator(
        df=df_iris,
        dataset_name="iris",
        ouptut_path=TEST_DATASETS_PATH,
        random_state=RANDOM_STATE,
    )

    df_wine = load_wine(return_X_y=False, as_frame=True)["frame"]  # type: ignore
    CSVTestDatasetGenerator(
        df=df_wine,
        dataset_name="wine",
        ouptut_path=TEST_DATASETS_PATH,
        random_state=RANDOM_STATE,
    )

    df_diabetes = load_diabetes(return_X_y=False, as_frame=True)["frame"]  # type: ignore
    CSVTestDatasetGenerator(
        df=df_diabetes,
        dataset_name="diabetes",
        ouptut_path=TEST_DATASETS_PATH,
        random_state=RANDOM_STATE,
    )


def _isclose(a: int, b: int, tol: int = 2) -> bool:
    return abs(a - b) <= tol


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params", "nrows", "ncols"),
    [
        (CSVDataLoader, CSV_IRIS_PATH / "comma.csv", {"separator": ","}, 150, 5),
        (CSVDataLoader, CSV_IRIS_PATH / "semicolon.csv", {"separator": ";"}, 150, 5),
        (CSVDataLoader, CSV_IRIS_PATH / "tab.csv", {"separator": "\t"}, 150, 5),
        (CSVDataLoader, CSV_IRIS_PATH / "vert_bar.csv", {"separator": "|"}, 150, 5),
        (CSVDataLoader, CSV_WINE_PATH / "comma.csv", {"separator": ","}, 178, 14),
        (CSVDataLoader, CSV_WINE_PATH / "semicolon.csv", {"separator": ";"}, 178, 14),
        (CSVDataLoader, CSV_WINE_PATH / "tab.csv", {"separator": "\t"}, 178, 14),
        (CSVDataLoader, CSV_WINE_PATH / "vert_bar.csv", {"separator": "|"}, 178, 14),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "comma.csv",
            {"separator": ","},
            442,
            11,
        ),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "semicolon.csv",
            {"separator": ";"},
            442,
            11,
        ),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "tab.csv",
            {"separator": "\t"},
            442,
            11,
        ),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "vert_bar.csv",
            {"separator": "|"},
            442,
            11,
        ),
        (JSONDataLoader, JSON_IRIS_PATH / "table.json", {"data_key": "data"}, 150, 5),
        (JSONDataLoader, JSON_IRIS_PATH / "records.json", {"data_key": None}, 150, 5),
        (
            JSONDataLoader,
            JSON_IRIS_PATH / "table_force_ascii.json",
            {"data_key": "data"},
            150,
            5,
        ),
    ],
    ids=[
        "test_load_csv_iris_comma",
        "test_load_csv_iris_semicolon",
        "test_load_csv_iris_tab",
        "test_load_csv_iris_vertical_bar",
        "test_load_csv_wine_comma",
        "test_load_csv_wine_semicolon",
        "test_load_csv_wine_tab",
        "test_load_csv_wine_vertical_bar",
        "test_load_csv_diabetes_comma",
        "test_load_csv_diabetes_semicolon",
        "test_load_csv_diabetes_tab",
        "test_load_csv_diabetes_vertical_bar",
        "test_load_json_iris_table",
        "test_load_json_iris_records",
        "test_load_json_iris_table_force_ascii_true",
    ],
)
def test_dataloader_from_file(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
    nrows: int,
    ncols: int,
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
    nrows : int
        Number of expected rows.
    ncols : int
        Number of expected columns.
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
    assert dataset["train"].num_rows == nrows
    assert dataset["train"].num_columns == ncols


@pytest.mark.parametrize(
    (
        "dataloader_cls",
        "dataset_path",
        "params",
        "train_nrows",
        "test_nrows",
        "val_nrows",
        "ncols",
    ),
    [
        (
            CSVDataLoader,
            CSV_IRIS_PATH / "split.zip",
            {"separator": ";"},
            50,
            50,
            50,
            5,
        ),
        (
            CSVDataLoader,
            CSV_WINE_PATH / "split.zip",
            {"separator": ";"},
            60,
            60,
            60,
            14,
        ),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "split.zip",
            {"separator": ";"},
            148,
            148,
            148,
            11,
        ),
        (
            CSVDataLoader,
            CSV_IRIS_PATH / "splits.zip",
            {"separator": ";"},
            50,
            50,
            50,
            5,
        ),
        (
            CSVDataLoader,
            CSV_WINE_PATH / "splits.zip",
            {"separator": ";"},
            60,
            60,
            60,
            14,
        ),
        (
            CSVDataLoader,
            CSV_DIABETES_PATH / "splits.zip",
            {"separator": ";"},
            148,
            148,
            148,
            11,
        ),
        # (JSONDataLoader, IRIS_JSON_PATH, {"data_key": "data"}),  # noqa: ERA001
    ],
    ids=[
        "test_load_csv_iris_from_zip",
        "test_load_csv_wine_from_zip",
        "test_load_csv_diabetes_from_zip",
        "test_load_csv_iris_from_batched_zip",
        "test_load_csv_wine_from_batched_zip",
        "test_load_csv_diabetes_from_batched_zip",
    ],
)
def test_dataloader_from_zip(
    dataloader_cls: Type[BaseDataLoader],
    dataset_path: str,
    params: Dict[str, Any],
    train_nrows: int,
    test_nrows: int,
    val_nrows: int,
    ncols: int,
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
    train_nrows : int
        Number of expected cols in the training set.
    test_nrows : int
        Number of expected cols in the test set.
    val_nrows : int
        Number of expected cols in the validatoin set.
    ncols : int
        Number of columns. It has to be the same in all splits.
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
    assert _isclose(dataset["train"].num_rows, train_nrows)
    assert dataset["train"].num_columns == ncols

    assert "test" in dataset
    assert _isclose(dataset["test"].num_rows, test_nrows)
    assert dataset["test"].num_columns == ncols

    assert "validation" in dataset
    assert _isclose(dataset["validation"].num_rows, val_nrows)
    assert dataset["validation"].num_columns == ncols


@pytest.mark.parametrize(
    ("dataloader_cls", "dataset_path", "params", "expected_error_msg"),
    [
        (
            CSVDataLoader,
            CSV_IRIS_PATH / "comma.csv",
            {},
            r"Error trying to load the CSV dataset: "
            r"separator parameter was not provided.",
        ),
        (
            CSVDataLoader,
            CSV_IRIS_PATH / "comma.csv",
            {"not_a_required_param": ","},
            r"Error trying to load the CSV dataset: "
            r"separator parameter was not provided.",
        ),
        # (
        #     JSONDataLoader,
        #     IRIS_JSON_PATH,
        #     {"not_a_valid_param": "data"},
        #     r"Error loading JSON file: data_key parameter was not provided.",
        # ),
    ],
    ids=[
        "test_load_csv_dataset_no_params",
        "test_load_csv_dataset_missing_separator_param",
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
        (CSVDataLoader, CSV_IRIS_PATH / "bad_format.csv", {"separator": ";"}),
        (CSVDataLoader, CSV_WINE_PATH / "bad_format.csv", {"separator": ";"}),
        (CSVDataLoader, CSV_DIABETES_PATH / "bad_format.csv", {"separator": ";"}),
    ],
    ids=[
        "test_load_csv_iris_with_bad_format_should_fail",
        "test_load_csv_wine_bad_with_format_should_fail",
        "test_load_csv_diabetes_bad_with_format_should_fail",
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
        match=r"An error occurred while generating the dataset",
    ):
        dataloder_instance.load_data(
            filepath_or_buffer=file,
            temp_path="tests/back/dataloaders",
            params=params,
        )
