import pathlib
from typing import Any, Dict

import pytest

from DashAI.back.dataloaders.classes.excel_dataloader import ExcelDataLoader
from tests.back.dataloaders.base_dataloader_tests import BaseDataLoaderTest

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")

EXCEL_IRIS_PATH = TEST_DATASETS_PATH / "excel" / "iris"
EXCEL_WINE_PATH = TEST_DATASETS_PATH / "excel" / "wine"
EXCEL_DIABETES_PATH = TEST_DATASETS_PATH / "excel" / "diabetes"


class TestCSVDataloader(BaseDataLoaderTest):
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
