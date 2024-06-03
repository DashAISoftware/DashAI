"""Tabular Dataloaders tests."""

import os
import pathlib

import pytest
from sklearn.datasets import load_diabetes, load_iris, load_wine

from tests.back.test_datasets_generator import (
    CSVTestDatasetGenerator,
    JSONTestDatasetGenerator,
)

TEST_DATASETS_PATH = pathlib.Path("tests/back/test_datasets")
CSV_IRIS_PATH = TEST_DATASETS_PATH / "csv" / "iris"
CSV_WINE_PATH = TEST_DATASETS_PATH / "csv" / "wine"
CSV_DIABETES_PATH = TEST_DATASETS_PATH / "csv" / "diabetes"
JSON_IRIS_PATH = TEST_DATASETS_PATH / "json" / "iris"
JSON_WINE_PATH = TEST_DATASETS_PATH / "json" / "wine"
JSON_DIABETES_PATH = TEST_DATASETS_PATH / "json" / "diabetes"


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
    JSONTestDatasetGenerator(
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
    JSONTestDatasetGenerator(
        df=df_diabetes,
        dataset_name="diabetes",
        ouptut_path=TEST_DATASETS_PATH,
        random_state=RANDOM_STATE,
    )
