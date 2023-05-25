import io

import pytest
from datasets import DatasetDict
from pyarrow.lib import ArrowInvalid
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset, save_dataset
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset


@pytest.fixture(scope="module", name="dataset_created")
def fixture_dataset():
    # Create DatasetDict from csv
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    yield datasetdict


def test_inputs_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = to_dashai_dataset(dataset_created, inputs_columns, outputs_columns)
    assert datasetdict["train"].inputs_columns == inputs_columns
    assert datasetdict["train"].outputs_columns == outputs_columns


def test_wrong_size_inputs_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species", "SepalWidthCm"]
    with pytest.raises(ValueError):
        to_dashai_dataset(dataset_created, inputs_columns, outputs_columns)


def test_undefined_inputs_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    with pytest.raises(ValueError):
        to_dashai_dataset(dataset_created, inputs_columns, outputs_columns)


def test_wrong_name_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    with pytest.raises(ValueError):
        to_dashai_dataset(dataset_created, inputs_columns, outputs_columns)


@pytest.fixture(scope="module", name="datasetdashai_created")
def fixture_datasetdashai():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    yield [datasetdict, dataloader_test]


def test_wrong_name_column(datasetdashai_created: list):
    tipos = {"Speci": "Categorical"}
    with pytest.raises(ValueError):
        for split in datasetdashai_created[0]:
            datasetdashai_created[0][split] = datasetdashai_created[0][
                split
            ].change_columns_type(tipos)


def test_wrong_type_column(datasetdashai_created: list):
    tipos = {"Species": "Numerical"}
    with pytest.raises(ArrowInvalid):
        for split in datasetdashai_created[0]:
            datasetdashai_created[0][split] = datasetdashai_created[0][
                split
            ].change_columns_type(tipos)


def test_datasetdashai_after_cast(datasetdashai_created: DatasetDict):
    inputs_columns = datasetdashai_created[0]["train"].inputs_columns
    tipos = {"Species": "Categorical"}
    for split in datasetdashai_created[0]:
        datasetdashai_created[0][split] = datasetdashai_created[0][
            split
        ].change_columns_type(tipos)
    assert datasetdashai_created[0]["train"].inputs_columns == inputs_columns


def test_split_dataset(datasetdashai_created: list):
    inputs_columns = datasetdashai_created[0]["train"].inputs_columns
    outputs_columns = datasetdashai_created[0]["train"].outputs_columns
    totals_rows = datasetdashai_created[0]["train"].num_rows
    separate_datasetdict = datasetdashai_created[1].split_dataset(
        datasetdashai_created[0], 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    train_rows = separate_datasetdict["train"].num_rows
    test_rows = separate_datasetdict["test"].num_rows
    validation_rows = separate_datasetdict["validation"].num_rows
    assert separate_datasetdict["train"].inputs_columns == inputs_columns
    assert separate_datasetdict["test"].inputs_columns == inputs_columns
    assert separate_datasetdict["validation"].inputs_columns == inputs_columns
    assert separate_datasetdict["train"].outputs_columns == outputs_columns
    assert separate_datasetdict["test"].outputs_columns == outputs_columns
    assert separate_datasetdict["validation"].outputs_columns == outputs_columns
    assert totals_rows == train_rows + test_rows + validation_rows


def separate_datasetdashai():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    return separate_datasetdict


def test_save_to_disk_and_load():
    separate_dataset = separate_datasetdashai()
    inputs_columns = separate_dataset["train"].inputs_columns
    outputs_columns = separate_dataset["train"].outputs_columns

    save_dataset(separate_dataset, "tests/back/dataloaders/dashaidataset")
    dashai_datasetdict = load_dataset("tests/back/dataloaders/dashaidataset")

    assert dashai_datasetdict["train"].inputs_columns == inputs_columns
    assert dashai_datasetdict["test"].inputs_columns == inputs_columns
    assert dashai_datasetdict["validation"].inputs_columns == inputs_columns
    assert dashai_datasetdict["train"].outputs_columns == outputs_columns
    assert dashai_datasetdict["validation"].outputs_columns == outputs_columns
    assert dashai_datasetdict["test"].outputs_columns == outputs_columns
