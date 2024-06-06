import pathlib
from typing import Any, Dict

import pytest

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseDataLoaderTest

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")

CSV_IRIS_PATH = TEST_DATASETS_PATH / "csv" / "iris"
CSV_WINE_PATH = TEST_DATASETS_PATH / "csv" / "wine"
CSV_DIABETES_PATH = TEST_DATASETS_PATH / "csv" / "diabetes"


class TestCSVDataloader(BaseDataLoaderTest):
    @property
    def dataloader_cls(self):
        return CSVDataLoader

    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            (CSV_IRIS_PATH / "comma.csv", {"separator": ","}, 150, 5),
            (CSV_IRIS_PATH / "semicolon.csv", {"separator": ";"}, 150, 5),
            (CSV_IRIS_PATH / "tab.csv", {"separator": "\t"}, 150, 5),
            (CSV_IRIS_PATH / "vert_bar.csv", {"separator": "|"}, 150, 5),
            (CSV_WINE_PATH / "comma.csv", {"separator": ","}, 178, 14),
            (CSV_WINE_PATH / "semicolon.csv", {"separator": ";"}, 178, 14),
            (CSV_WINE_PATH / "tab.csv", {"separator": "\t"}, 178, 14),
            (CSV_WINE_PATH / "vert_bar.csv", {"separator": "|"}, 178, 14),
            (CSV_DIABETES_PATH / "comma.csv", {"separator": ","}, 442, 11),
            (CSV_DIABETES_PATH / "semicolon.csv", {"separator": ";"}, 442, 11),
            (CSV_DIABETES_PATH / "tab.csv", {"separator": "\t"}, 442, 11),
            (CSV_DIABETES_PATH / "vert_bar.csv", {"separator": "|"}, 442, 11),
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
        ],
    )
    def test_load_data_from_file(
        self,
        dataset_path: str,
        params: Dict[str, Any],
        nrows: int,
        ncols: int,
    ) -> None:
        super().test_load_data_from_file(
            dataset_path=dataset_path,
            params=params,
            nrows=nrows,
            ncols=ncols,
        )

    @pytest.mark.parametrize(
        (
            "dataset_path",
            "params",
            "train_nrows",
            "test_nrows",
            "val_nrows",
            "ncols",
        ),
        [
            (CSV_IRIS_PATH / "split.zip", {"separator": ";"}, 50, 50, 50, 5),
            (CSV_WINE_PATH / "split.zip", {"separator": ";"}, 60, 60, 60, 14),
            (CSV_DIABETES_PATH / "split.zip", {"separator": ";"}, 148, 148, 148, 11),
            (CSV_IRIS_PATH / "splits.zip", {"separator": ";"}, 50, 50, 50, 5),
            (CSV_WINE_PATH / "splits.zip", {"separator": ";"}, 60, 60, 60, 14),
            (CSV_DIABETES_PATH / "splits.zip", {"separator": ";"}, 148, 148, 148, 11),
        ],
        ids=[
            "test_load_csv_iris_from_split_zip",
            "test_load_csv_wine_from_split_zip",
            "test_load_csv_diabetes_from_split_zip",
            "test_load_csv_iris_from_batched_split_zip",
            "test_load_csv_wine_from_batched_split_zip",
            "test_load_csv_diabetes_from_batched_split_zip",
        ],
    )
    def test_load_data_from_zip(
        self,
        dataset_path: str,
        params: Dict[str, Any],
        train_nrows: int,
        test_nrows: int,
        val_nrows: int,
        ncols: int,
    ):
        super().test_load_data_from_zip(
            dataset_path=dataset_path,
            params=params,
            train_nrows=train_nrows,
            test_nrows=test_nrows,
            val_nrows=val_nrows,
            ncols=ncols,
        )

    @pytest.mark.parametrize(
        (
            "dataset_path",
            "params",
            "expected_error_msg",
        ),
        [
            (
                CSV_IRIS_PATH / "comma.csv",
                {},
                r"Error trying to load the CSV dataset: "
                r"separator parameter was not provided.",
            ),
            (
                CSV_IRIS_PATH / "comma.csv",
                {"not_a_required_param": ","},
                r"Error trying to load the CSV dataset: "
                r"separator parameter was not provided.",
            ),
        ],
        ids=[
            "test_load_csv_dataset_no_params",
            "test_load_csv_dataset_missing_separator_param",
        ],
    )
    def test_dataloader_with_missing_required_params(
        self,
        dataset_path: str,
        params: Dict[str, Any],
        expected_error_msg: str,
    ):
        super().test_dataloader_with_missing_required_params(
            dataset_path=dataset_path,
            params=params,
            expected_error_msg=expected_error_msg,
        )

    @pytest.mark.parametrize(
        ("dataset_path", "params"),
        [
            (CSV_IRIS_PATH / "bad_format.csv", {"separator": ";"}),
            (CSV_WINE_PATH / "bad_format.csv", {"separator": ";"}),
            (CSV_DIABETES_PATH / "bad_format.csv", {"separator": ";"}),
        ],
        ids=[
            "test_load_csv_iris_with_bad_format",
            "test_load_csv_wine_with_bad_format",
            "test_load_csv_diabetes_with_bad_format",
        ],
    )
    def test_dataloader_try_to_load_a_invalid_datasets(
        self,
        dataset_path: str,
        params: Dict[str, Any],
    ):
        super().test_dataloader_try_to_load_a_invalid_datasets(
            dataset_path=dataset_path,
            params=params,
        )
