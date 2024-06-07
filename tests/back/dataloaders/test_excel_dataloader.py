"""Excel dataloader test set module."""

import pathlib
from typing import Any, Dict

import pytest
from sklearn.datasets import load_diabetes, load_iris, load_wine

from DashAI.back.dataloaders.classes.excel_dataloader import ExcelDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseTabularDataLoaderTester
from tests.back.test_datasets_generator import ExcelTestDatasetGenerator


class TestExcelDataloader(BaseTabularDataLoaderTester):
    @property
    def dataloader_cls(self):
        return ExcelDataLoader

    @pytest.fixture(scope="module", autouse=True)
    def _setup(self, test_datasets_path: pathlib.Path, random_state: int) -> None:
        """Generate the excel test datasets."""

        df_iris = load_iris(return_X_y=False, as_frame=True)["frame"]  # type: ignore
        df_wine = load_wine(return_X_y=False, as_frame=True)["frame"]  # type: ignore
        df_diabetes = load_diabetes(return_X_y=False, as_frame=True)["frame"]  # type: ignore

        test_datasets = [
            (df_iris, "iris"),
            (df_wine, "wine"),
            (df_diabetes, "diabetes"),
        ]

        for df, name in test_datasets:
            ExcelTestDatasetGenerator(
                df=df,
                dataset_name=name,
                ouptut_path=test_datasets_path,
                random_state=random_state,
            )

    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            (
                "iris/basic.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                150,
                5,
            ),
            (
                "iris/with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                150,
                5,
            ),
            (
                "iris/no_header.xlsx",
                {"sheet": 0, "header": None, "usecols": None},
                150,
                5,
            ),
            ("wine/basic.xlsx", {"sheet": 0, "header": 0, "usecols": None}, 178, 14),
            (
                "wine/with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                178,
                14,
            ),
            (
                "wine/no_header.xlsx",
                {"sheet": 0, "header": None, "usecols": None},
                178,
                14,
            ),
            (
                "diabetes/basic.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                442,
                11,
            ),
            (
                "diabetes/with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                442,
                11,
            ),
            (
                "diabetes/no_header.xlsx",
                {"sheet": 0, "header": None, "usecols": None},
                442,
                11,
            ),
        ],
        ids=[
            "test_load_excel_iris_basic",
            "test_load_excel_iris_with_sheet_name",
            "test_load_excel_iris_no_header",
            "test_load_excel_wine_basic",
            "test_load_excel_wine_with_sheet_name",
            "test_load_excel_wine_no_header",
            "test_load_excel_diabetes_basic",
            "test_load_excel_diabetes_with_sheet_name",
            "test_load_excel_diabetes_no_header",
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
            dataset_path=test_datasets_path / "excel" / dataset_path,
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
            (
                "iris/split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                50,
                50,
                50,
                5,
            ),
            (
                "wine/split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                60,
                60,
                60,
                14,
            ),
            (
                "diabetes/split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                148,
                148,
                148,
                11,
            ),
            (
                "iris/splits.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                50,
                50,
                50,
                5,
            ),
            (
                "wine/splits.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                60,
                60,
                60,
                14,
            ),
            (
                "diabetes/splits.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                148,
                148,
                148,
                11,
            ),
        ],
        ids=[
            "test_load_excel_iris_from_split_zip",
            "test_load_excel_wine_from_split_zip",
            "test_load_excel_diabetes_from_split_zip",
            "test_load_excel_iris_from_batched_split_zip",
            "test_load_excel_wine_from_batched_split_zip",
            "test_load_excel_diabetes_from_batched_split_zip",
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
            dataset_path=test_datasets_path / "excel" / dataset_path,
            params=params,
            train_nrows=train_nrows,
            test_nrows=test_nrows,
            val_nrows=val_nrows,
            ncols=ncols,
        )

    # TODO: Delete this test and change to schema automated verification.
    @pytest.mark.parametrize(
        ("dataset_path", "params", "expected_error_msg"),
        [("", {}, "")],
    )
    def test_dataloader_with_missing_required_params(
        self,
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
        expected_error_msg: str,
    ) -> None:
        pass

    @pytest.mark.parametrize(
        ("dataset_path", "params"),
        [
            ("iris/bad_format.xlsx", {"sheet": 0, "header": 0, "usecols": None}),
            ("wine/bad_format.xlsx", {"sheet": 0, "header": 0, "usecols": None}),
            ("diabetes/bad_format.xlsx", {"sheet": 0, "header": 0, "usecols": None}),
        ],
        ids=[
            "test_load_excel_iris_with_bad_format",
            "test_load_excel_wine_with_bad_format",
            "test_load_excel_diabetes_with_bad_format",
        ],
    )
    def test_dataloader_try_to_load_a_invalid_datasets(
        self,
        test_datasets_path: pathlib.Path,
        dataset_path: str,
        params: Dict[str, Any],
    ):
        super().test_dataloader_try_to_load_a_invalid_datasets(
            dataset_path=test_datasets_path / "excel" / dataset_path,
            params=params,
        )
