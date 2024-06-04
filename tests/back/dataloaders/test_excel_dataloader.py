import pathlib
from typing import Any, Dict

import pytest

from DashAI.back.dataloaders.classes.excel_dataloader import ExcelDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseDataLoaderTest

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")

EXCEL_IRIS_PATH = TEST_DATASETS_PATH / "excel" / "iris"
EXCEL_WINE_PATH = TEST_DATASETS_PATH / "excel" / "wine"
EXCEL_DIABETES_PATH = TEST_DATASETS_PATH / "excel" / "diabetes"


class TestExcelDataloader(BaseDataLoaderTest):
    @pytest.mark.parametrize(
        ("dataset_path", "params", "nrows", "ncols"),
        [
            (
                EXCEL_IRIS_PATH / "basic.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                150,
                5,
            ),
            (
                EXCEL_IRIS_PATH / "with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                150,
                5,
            ),
            (
                EXCEL_IRIS_PATH / "no_header.xlsx",
                {"sheet": 0, "header": None, "usecols": None},
                150,
                5,
            ),
            (
                EXCEL_WINE_PATH / "basic.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                178,
                14,
            ),
            (
                EXCEL_WINE_PATH / "with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                178,
                14,
            ),
            (
                EXCEL_WINE_PATH / "no_header.xlsx",
                {"sheet": 0, "header": None, "usecols": None},
                178,
                14,
            ),
            (
                EXCEL_DIABETES_PATH / "basic.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                442,
                11,
            ),
            (
                EXCEL_DIABETES_PATH / "with_sheet_name.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
                442,
                11,
            ),
            (
                EXCEL_DIABETES_PATH / "no_header.xlsx",
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
        dataset_path: str,
        params: Dict[str, Any],
        nrows: int,
        ncols: int,
    ) -> None:
        super().test_load_data_from_file(
            dataloader_cls=ExcelDataLoader,
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
            (
                EXCEL_IRIS_PATH / "split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                50,
                50,
                50,
                5,
            ),
            (
                EXCEL_WINE_PATH / "split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                60,
                60,
                60,
                14,
            ),
            (
                EXCEL_DIABETES_PATH / "split.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                148,
                148,
                148,
                11,
            ),
            (
                EXCEL_IRIS_PATH / "splits.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                50,
                50,
                50,
                5,
            ),
            (
                EXCEL_WINE_PATH / "splits.zip",
                {"sheet": 0, "header": 0, "usecols": None},
                60,
                60,
                60,
                14,
            ),
            (
                EXCEL_DIABETES_PATH / "splits.zip",
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
        dataset_path: str,
        params: Dict[str, Any],
        train_nrows: int,
        test_nrows: int,
        val_nrows: int,
        ncols: int,
    ):
        super().test_load_data_from_zip(
            dataloader_cls=ExcelDataLoader,
            dataset_path=dataset_path,
            params=params,
            train_nrows=train_nrows,
            test_nrows=test_nrows,
            val_nrows=val_nrows,
            ncols=ncols,
        )

    @pytest.mark.parametrize(
        ("dataset_path", "params"),
        [
            (
                EXCEL_IRIS_PATH / "bad_format.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
            ),
            (
                EXCEL_WINE_PATH / "bad_format.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
            ),
            (
                EXCEL_DIABETES_PATH / "bad_format.xlsx",
                {"sheet": 0, "header": 0, "usecols": None},
            ),
        ],
        ids=[
            "test_load_excel_iris_with_bad_format",
            "test_load_excel_wine_with_bad_format",
            "test_load_excel_diabetes_with_bad_format",
        ],
    )
    def test_dataloader_try_to_load_a_invalid_datasets(
        self,
        dataset_path: str,
        params: Dict[str, Any],
    ):
        super().test_dataloader_try_to_load_a_invalid_datasets(
            dataloader_cls=ExcelDataLoader,
            dataset_path=dataset_path,
            params=params,
        )
