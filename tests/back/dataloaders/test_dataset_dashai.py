import io

import pytest
from datasets import DatasetDict
from pyarrow.lib import ArrowInvalid
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataset_dashai import DatasetDashAI


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
    yield [datasetdict, dataloader_test]


def test_inputs_outputs_columns(dataset_created: list):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = dataset_created[1].to_dataset_dashai(
        dataset_created[0], inputs_columns, outputs_columns
    )
    assert datasetdict["train"].inputs_columns == inputs_columns
    assert datasetdict["train"].outputs_columns == outputs_columns


def test_wrong_size_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = [
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ]
        outputs_columns = ["Species", "SepalWidthCm"]
        dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_undefined_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_wrong_name_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


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
    datasetdict = dataloader_test.to_dataset_dashai(
        datasetdict, inputs_columns, outputs_columns
    )
    yield [datasetdict, dataloader_test]


def test_wrong_name_column(datasetdashai_created: list):
    with pytest.raises(ValueError):
        tipos = {"Speci": "Categorico"}
        for split in datasetdashai_created[0]:
            datasetdashai_created[0][split] = datasetdashai_created[0][
                split
            ].change_columns_type(tipos)
    assert True


def test_wrong_type_column(datasetdashai_created: list):
    with pytest.raises(ArrowInvalid):
        tipos = {"Species": "Numerico"}
        for split in datasetdashai_created[0]:
            datasetdashai_created[0][split] = datasetdashai_created[0][
                split
            ].change_columns_type(tipos)
    assert True


def test_datasetdashai_after_cast(datasetdashai_created: DatasetDict):
    inputs_columns = datasetdashai_created[0]["train"].inputs_columns
    tipos = {"Species": "Categorico"}
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
    datasetdict = dataloader_test.to_dataset_dashai(
        datasetdict, inputs_columns, outputs_columns
    )
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    return separate_datasetdict


def test_save_to_disk_and_load():
    separate_dataset = separate_datasetdashai()
    inputs_columns = separate_dataset["train"].inputs_columns
    outputs_columns = separate_dataset["train"].outputs_columns

    for i in separate_dataset.keys():
        separate_dataset[i].save_to_disk(f"tests/back/dataloaders/datasetdashai_{i}")
    paths = {
        "path_train": "tests/back/dataloaders/datasetdashai_train",
        "path_val": "tests/back/dataloaders/datasetdashai_validation",
        "path_test": "tests/back/dataloaders/datasetdashai_test",
    }

    datasetdashai_train = DatasetDashAI.load_from_disk(paths["path_train"])
    datasetdashai_val = DatasetDashAI.load_from_disk(paths["path_val"])
    datasetdashai_test = DatasetDashAI.load_from_disk(paths["path_test"])
    datasetdict_dashai = DatasetDict(
        {
            "train": datasetdashai_train,
            "validation": datasetdashai_val,
            "test": datasetdashai_test,
        }
    )
    assert datasetdict_dashai["train"].inputs_columns == inputs_columns
    assert datasetdict_dashai["test"].inputs_columns == inputs_columns
    assert datasetdict_dashai["validation"].inputs_columns == inputs_columns
    assert datasetdict_dashai["train"].outputs_columns == outputs_columns
    assert datasetdict_dashai["validation"].outputs_columns == outputs_columns
    assert datasetdict_dashai["test"].outputs_columns == outputs_columns
