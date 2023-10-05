import io

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.preprocessor.column_dropper_by_name import ColumnDropperByName


@pytest.fixture(scope="module", name="iris_dataset")
def prepare_iris_dataset():
    test_dataset_path = "tests/back/preprocessor/iris.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/preprocessor",
        params={"separator": ","},
    )

    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]

    datasetdict = to_dashai_dataset(
        datasetdict,
        inputs_columns,
        outputs_columns=["Species"],
    )

    return datasetdict


@pytest.fixture(scope="module", name="iris_dataset_petal_width_dropped")
def prepare_iris_petal_width_dropped_dataset():
    test_dataset_path = "tests/back/preprocessor/iris_petal_width_dropped.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/preprocessor",
        params={"separator": ","},
    )

    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm"]

    datasetdict = to_dashai_dataset(
        datasetdict,
        inputs_columns,
        outputs_columns=["Species"],
    )

    return datasetdict


def test_remove_input_column_with_column_name(
    iris_dataset: DatasetDict, iris_dataset_petal_width_dropped: DatasetDict
):
    dropper = ColumnDropperByName("PetalWidthCm")
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