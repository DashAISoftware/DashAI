import pathlib
from typing import Any, Dict

import pytest

from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseTabularDataLoaderTester

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")

JSON_IRIS_PATH = TEST_DATASETS_PATH / "json" / "iris"
JSON_WINE_PATH = TEST_DATASETS_PATH / "json" / "wine"
JSON_DIABETES_PATH = TEST_DATASETS_PATH / "json" / "diabetes"


class TestJSONDataLoader(BaseTabularDataLoaderTester):
    @property
    def dataloader_cls(self):
        return JSONDataLoader

    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            (JSON_IRIS_PATH / "table.json", {"data_key": "data"}, 150, 5),
            (JSON_IRIS_PATH / "records.json", {"data_key": None}, 150, 5),
            (JSON_IRIS_PATH / "table_force_ascii.json", {"data_key": "data"}, 150, 5),
            (JSON_WINE_PATH / "table.json", {"data_key": "data"}, 178, 14),
            (JSON_WINE_PATH / "records.json", {"data_key": None}, 178, 14),
            (JSON_WINE_PATH / "table_force_ascii.json", {"data_key": "data"}, 178, 14),
            (JSON_DIABETES_PATH / "table.json", {"data_key": "data"}, 442, 11),
            (JSON_DIABETES_PATH / "records.json", {"data_key": None}, 442, 11),
            (
                JSON_DIABETES_PATH / "table_force_ascii.json",
                {"data_key": "data"},
                442,
                11,
            ),
        ],
        ids=[
            "test_load_json_iris_table",
            "test_load_json_iris_records",
            "test_load_json_iris_table_force_ascii_true",
            "test_load_json_wine_table",
            "test_load_json_wine_records",
            "test_load_json_wine_table_force_ascii_true",
            "test_load_json_diabetes_table",
            "test_load_json_diabetes_records",
            "test_load_json_diabetes_table_force_ascii_true",
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
            (JSON_IRIS_PATH / "split.zip", {"data_key": "data"}, 50, 50, 50, 5),
            (JSON_WINE_PATH / "split.zip", {"data_key": "data"}, 60, 60, 60, 14),
            (JSON_DIABETES_PATH / "split.zip", {"data_key": "data"}, 148, 148, 148, 11),
            (JSON_IRIS_PATH / "splits.zip", {"data_key": "data"}, 50, 50, 50, 5),
            (JSON_WINE_PATH / "splits.zip", {"data_key": "data"}, 60, 60, 60, 14),
            (
                JSON_DIABETES_PATH / "splits.zip",
                {"data_key": "data"},
                148,
                148,
                148,
                11,
            ),
        ],
        ids=[
            "test_load_json_iris_from_split_zip",
            "test_load_json_wine_from_split_zip",
            "test_load_json_diabetes_from_split_zip",
            "test_load_json_iris_from_batched_split_zip",
            "test_load_json_wine_from_batched_split_zip",
            "test_load_json_diabetes_from_batched_split_zip",
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
                JSON_IRIS_PATH / "table.json",
                {},
                r"Error trying to load the JSON dataset: "
                r"data_key parameter was not provided.",
            ),
            (
                JSON_IRIS_PATH / "table.json",
                {"not_a_valid_param": "data"},
                r"Error trying to load the JSON dataset: "
                r"data_key parameter was not provided.",
            ),
        ],
        ids=[
            "test_load_json_dataset_no_params",
            "test_load_json_dataset_missing_separator_param",
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
            (JSON_IRIS_PATH / "bad_format.json", {"data_key": "data"}),
            (JSON_WINE_PATH / "bad_format.json", {"data_key": "data"}),
            (JSON_DIABETES_PATH / "bad_format.json", {"data_key": "data"}),
        ],
        ids=[
            "test_load_json_iris_with_bad_format",
            "test_load_json_wine_with_bad_format",
            "test_load_json_diabetes_with_bad_format",
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
