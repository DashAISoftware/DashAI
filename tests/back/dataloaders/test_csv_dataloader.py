"""CSV DataLoader tests module."""

import pathlib
from typing import Any, Dict

import pytest
from sklearn.datasets import load_diabetes, load_iris, load_wine

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from tests.back.dataloaders.base_tabular_dataloader_tests import (
    BaseTabularDataLoaderTester,
)
from tests.back.test_datasets_generator import CSVTestDatasetGenerator

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")


@pytest.fixture(scope="module", autouse=True)
def _setup(test_datasets_path: pathlib.Path, random_state: int) -> None:
    """Generate the CSV test datasets."""

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


class TestCSVDataloader(BaseTabularDataLoaderTester):
    @property
    def dataloader_cls(self):
        return CSVDataLoader

    @property
    def data_type_name(self):
        return "csv"

    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            ("iris/comma.csv", {"separator": ","}, 150, 5),
            ("iris/semicolon.csv", {"separator": ";"}, 150, 5),
            ("iris/tab.csv", {"separator": "\t"}, 150, 5),
            ("iris/vert_bar.csv", {"separator": "|"}, 150, 5),
            ("wine/comma.csv", {"separator": ","}, 178, 14),
            ("wine/semicolon.csv", {"separator": ";"}, 178, 14),
            ("wine/tab.csv", {"separator": "\t"}, 178, 14),
            ("wine/vert_bar.csv", {"separator": "|"}, 178, 14),
            ("diabetes/comma.csv", {"separator": ","}, 442, 11),
            ("diabetes/semicolon.csv", {"separator": ";"}, 442, 11),
            ("diabetes/tab.csv", {"separator": "\t"}, 442, 11),
            ("diabetes/vert_bar.csv", {"separator": "|"}, 442, 11),
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        nrows: int,
        ncols: int,
    ) -> None:
        super().test_load_data_from_file(
            dataset_path=test_datasets_path / self.data_type_name / dataset_path,
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
            ("iris/split.zip", {"separator": ";"}, 50, 50, 50, 5),
            ("wine/split.zip", {"separator": ";"}, 60, 60, 60, 14),
            ("diabetes/split.zip", {"separator": ";"}, 148, 148, 148, 11),
            ("iris/splits.zip", {"separator": ";"}, 50, 50, 50, 5),
            ("wine/splits.zip", {"separator": ";"}, 60, 60, 60, 14),
            ("diabetes/splits.zip", {"separator": ";"}, 148, 148, 148, 11),
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        train_nrows: int,
        test_nrows: int,
        val_nrows: int,
        ncols: int,
    ):
        super().test_load_data_from_zip(
            dataset_path=test_datasets_path / self.data_type_name / dataset_path,
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
                "iris/comma.csv",
                {},
                r"Error trying to load the CSV dataset: "
                r"separator parameter was not provided.",
            ),
            (
                "iris/comma.csv",
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
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        expected_error_msg: str,
    ):
        super().test_dataloader_with_missing_required_params(
            dataset_path=test_datasets_path / self.data_type_name / dataset_path,
            params=params,
            expected_error_msg=expected_error_msg,
        )

    @pytest.mark.parametrize(
        ("dataset_path", "params"),
        [
            ("iris/bad_format.csv", {"separator": ";"}),
            ("wine/bad_format.csv", {"separator": ";"}),
            ("diabetes/bad_format.csv", {"separator": ";"}),
        ],
        ids=[
            "test_load_csv_iris_with_bad_format",
            "test_load_csv_wine_with_bad_format",
            "test_load_csv_diabetes_with_bad_format",
        ],
    )
    def test_dataloader_try_to_load_a_invalid_datasets(
        self,
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
    ):
        super().test_dataloader_try_to_load_a_invalid_datasets(
            dataset_path=test_datasets_path / self.data_type_name / dataset_path,
            params=params,
        )
