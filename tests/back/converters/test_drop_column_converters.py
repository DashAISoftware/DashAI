import io

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.converters.column_dropper_by_index import ColumnDropperByIndex
from DashAI.back.converters.column_dropper_by_name import ColumnDropperByName
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    to_dashai_dataset,
)


@pytest.fixture(name="iris_dataset")
def prepare_iris_dataset():
    test_dataset_path = "tests/back/converters/iris.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/converters",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(datasetdict)

    return datasetdict


@pytest.fixture(name="iris_dataset_petal_width_dropped")
def prepare_iris_petal_width_dropped_dataset():
    test_dataset_path = "tests/back/converters/iris_petal_width_dropped.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/converters",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(datasetdict)

    return datasetdict


@pytest.fixture(name="iris_dataset_petal_cols_dropped")
def prepare_iris_dataset_petal_cols_dropped():
    test_dataset_path = "tests/back/converters/iris_petal_cols_dropped.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/converters",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(datasetdict)

    return datasetdict


def test_remove_input_column_with_column_name(
    iris_dataset: DatasetDict, iris_dataset_petal_width_dropped: DatasetDict
):
    dropper = ColumnDropperByName(column_names="PetalWidthCm")
    print(iris_dataset)
    dataset_obtained = dropper.transform(iris_dataset)
    assert set(dataset_obtained.keys()) == set(iris_dataset_petal_width_dropped.keys())
    for split in dataset_obtained:
        dataset_split: DashAIDataset = dataset_obtained[split]
        iris_dataset_dropped_split: DashAIDataset = iris_dataset_petal_width_dropped[
            split
        ]
        assert len(dataset_split) == len(iris_dataset_dropped_split)
        for column_name in dataset_split.column_names:
            assert dataset_split[column_name] == iris_dataset_dropped_split[column_name]
        assert dataset_split.features == iris_dataset_dropped_split.features


def test_remove_input_column_with_index(
    iris_dataset: DatasetDict, iris_dataset_petal_width_dropped: DatasetDict
):
    dropper = ColumnDropperByIndex(columns_index=3)
    dataset_obtained = dropper.transform(iris_dataset)
    assert set(dataset_obtained.keys()) == set(iris_dataset_petal_width_dropped.keys())
    for split in dataset_obtained:
        dataset_split: DashAIDataset = dataset_obtained[split]
        iris_dataset_dropped_split: DashAIDataset = iris_dataset_petal_width_dropped[
            split
        ]
        assert len(dataset_split) == len(iris_dataset_dropped_split)
        for column_name in dataset_split.column_names:
            assert dataset_split[column_name] == iris_dataset_dropped_split[column_name]
        assert dataset_split.features == iris_dataset_dropped_split.features


def test_remove_2_input_columns_with_column_names(
    iris_dataset: DatasetDict, iris_dataset_petal_cols_dropped: DatasetDict
):
    dropper = ColumnDropperByName(column_names=["PetalLengthCm", "PetalWidthCm"])
    dataset_obtained = dropper.transform(iris_dataset)
    assert set(dataset_obtained.keys()) == set(iris_dataset_petal_cols_dropped.keys())
    for split in dataset_obtained:
        dataset_split: DashAIDataset = dataset_obtained[split]
        iris_dataset_dropped_split: DashAIDataset = iris_dataset_petal_cols_dropped[
            split
        ]
        assert len(dataset_split) == len(iris_dataset_dropped_split)
        for column_name in dataset_split.column_names:
            assert dataset_split[column_name] == iris_dataset_dropped_split[column_name]
        assert dataset_split.features == iris_dataset_dropped_split.features


def test_remove_2_input_columns_with_index(
    iris_dataset: DatasetDict, iris_dataset_petal_cols_dropped: DatasetDict
):
    dropper = ColumnDropperByIndex(columns_index=(2, 3))
    dataset_obtained = dropper.transform(iris_dataset)
    assert set(dataset_obtained.keys()) == set(iris_dataset_petal_cols_dropped.keys())
    for split in dataset_obtained:
        dataset_split: DashAIDataset = dataset_obtained[split]
        iris_dataset_dropped_split: DashAIDataset = iris_dataset_petal_cols_dropped[
            split
        ]
        assert len(dataset_split) == len(iris_dataset_dropped_split)
        for column_name in dataset_split.column_names:
            assert dataset_split[column_name] == iris_dataset_dropped_split[column_name]
        assert dataset_split.features == iris_dataset_dropped_split.features
