"""JSON DataLoader tests module."""

import pathlib
from typing import Any, Dict

import pytest
from sklearn.datasets import load_diabetes, load_iris, load_wine

from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseTabularDataLoaderTester
from tests.back.test_datasets_generator import CSVTestDatasetGenerator

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")


class TestJSONDataLoader(BaseTabularDataLoaderTester):
    @property
    def dataloader_cls(self):
        return JSONDataLoader

    @pytest.fixture(scope="module", autouse=True)
    def _setup(self, test_datasets_path: pathlib.Path, random_state: int) -> None:
        """Generate the json test datasets."""

        df_iris = load_iris(return_X_y=False, as_frame=True)["frame"]  # type: ignore
        df_wine = load_wine(return_X_y=False, as_frame=True)["frame"]  # type: ignore
        df_diabetes = load_diabetes(return_X_y=False, as_frame=True)["frame"]  # type: ignore

        test_datasets = [
            (df_iris, "iris"),
            (df_wine, "wine"),
            (df_diabetes, "diabetes"),
        ]

        for df, name in test_datasets:
            CSVTestDatasetGenerator(
                df=df,
                dataset_name=name,
                ouptut_path=test_datasets_path,
                random_state=random_state,
            )

    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            ("iris/table.json", {"data_key": "data"}, 150, 5),
            ("iris/records.json", {"data_key": None}, 150, 5),
            ("iris/table_force_ascii.json", {"data_key": "data"}, 150, 5),
            ("wine/table.json", {"data_key": "data"}, 178, 14),
            ("wine/records.json", {"data_key": None}, 178, 14),
            ("wine/table_force_ascii.json", {"data_key": "data"}, 178, 14),
            ("diabetes/table.json", {"data_key": "data"}, 442, 11),
            ("diabetes/records.json", {"data_key": None}, 442, 11),
            (
                "diabetes/table_force_ascii.json",
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        nrows: int,
        ncols: int,
    ) -> None:
        super().test_load_data_from_file(
            dataset_path=test_datasets_path / "json" / dataset_path,
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
            ("iris/split.zip", {"data_key": "data"}, 50, 50, 50, 5),
            ("wine/split.zip", {"data_key": "data"}, 60, 60, 60, 14),
            ("diabetes/split.zip", {"data_key": "data"}, 148, 148, 148, 11),
            ("iris/splits.zip", {"data_key": "data"}, 50, 50, 50, 5),
            ("wine/splits.zip", {"data_key": "data"}, 60, 60, 60, 14),
            ("diabetes/splits.zip", {"data_key": "data"}, 148, 148, 148, 11),
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        train_nrows: int,
        test_nrows: int,
        val_nrows: int,
        ncols: int,
    ):
        super().test_load_data_from_zip(
            dataset_path=test_datasets_path / "json" / dataset_path,
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
                "iris/table.json",
                {},
                r"Error trying to load the JSON dataset: "
                r"data_key parameter was not provided.",
            ),
            (
                "iris/table.json",
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        expected_error_msg: str,
    ):
        super().test_dataloader_with_missing_required_params(
            dataset_path=test_datasets_path / "json" / dataset_path,
            params=params,
            expected_error_msg=expected_error_msg,
        )

    @pytest.mark.parametrize(
        ("dataset_path", "params"),
        [
            ("iris/bad_format.json", {"data_key": "data"}),
            ("wine/bad_format.json", {"data_key": "data"}),
            ("diabetes/bad_format.json", {"data_key": "data"}),
        ],
        ids=[
            "test_load_json_iris_with_bad_format",
            "test_load_json_wine_with_bad_format",
            "test_load_json_diabetes_with_bad_format",
        ],
    )
    def test_dataloader_try_to_load_a_invalid_datasets(
        self,
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
    ):
        super().test_dataloader_try_to_load_a_invalid_datasets(
            dataset_path=test_datasets_path / "json" / dataset_path,
            params=params,
        )
