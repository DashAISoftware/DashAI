import io
import shutil

import pytest
from datasets import ClassLabel, DatasetDict
from pyarrow.lib import ArrowInvalid
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    divide_by_columns,
    load_dataset,
    save_dataset,
    validate_inputs_outputs,
)
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset


@pytest.fixture(scope="module", name="dataset_created")
def fixture_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    csv_dataloader = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = csv_dataloader.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params=params,
    )

    return datasetdict


def test_wrong_size_inputs_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species", "SepalWidthCm"]
    with pytest.raises(
        ValueError,
        match=(
            r"Inputs and outputs cannot have more elements than names. Number of "
            r"inputs: 4, number of outputs: 2, number of names: 5. "
        ),
    ):
        validate_inputs_outputs(dataset_created, inputs_columns, outputs_columns)


def test_wrong_name_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    with pytest.raises(
        ValueError,
        match=r"Inputs and outputs can only contain elements that exist in names.",
    ):
        validate_inputs_outputs(dataset_created, inputs_columns, outputs_columns)


@pytest.fixture(scope="module", name="dashaidataset_created")
def fixture_dashaidataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    csv_dataloader = CSVDataLoader()
    params = {"separator": ","}

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = csv_dataloader.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params=params,
    )

    datasetdict = to_dashai_dataset(datasetdict)

    return [datasetdict, csv_dataloader]


def test_dashaidataset_sample(dashaidataset_created: list):
    methods = ["head", "tail", "random"]
    n_samples = [1, 10]

    for split in dashaidataset_created[0]:
        dataset = dashaidataset_created[0][split]

        for n in n_samples:
            for method in methods:
                sample = dataset.sample(n=n, method=method)
                values = list(sample.values())
                len_items = len(values[0])
                assert all(len(item) == len_items for item in values)

                if method == "head":
                    assert sample == dataset[:n]

                elif method == "tail":
                    assert sample == dataset[-n:]

                elif method == "random":
                    for index in list(range(len_items)):
                        one_sample = {key: None for key in sample}
                        for key in one_sample:
                            one_sample[key] = sample[key][index]
                        assert any(one_sample == data for data in dataset)


def test_wrong_name_column(dashaidataset_created: list):
    col_types = {"Speci": "Categorical"}

    for split in dashaidataset_created[0]:
        with pytest.raises(
            ValueError,
            match=(
                r"Error while changing column types: column 'Speci' does not "
                r"exist in dataset."
            ),
        ):
            dashaidataset_created[0][split] = dashaidataset_created[0][
                split
            ].change_columns_type(col_types)


def test_wrong_type_column(dashaidataset_created: list):
    col_types = {"Species": "Numerical"}

    for split in dashaidataset_created[0]:
        with pytest.raises(ArrowInvalid):
            dashaidataset_created[0][split] = dashaidataset_created[0][
                split
            ].change_columns_type(col_types)


def test_dashaidataset_after_cast(dashaidataset_created: DatasetDict):
    features = dashaidataset_created[0]["train"].features.copy()
    features["Species"] = ClassLabel(
        names=list(set(dashaidataset_created[0]["train"]["Species"]))
    )

    col_types = {"Species": "Categorical"}
    for split in dashaidataset_created[0]:
        dashaidataset_created[0][split] = dashaidataset_created[0][
            split
        ].change_columns_type(col_types)
    assert dashaidataset_created[0]["train"].features == features


def test_split_dataset(dashaidataset_created: list):
    totals_rows = dashaidataset_created[0]["train"].num_rows
    separate_datasetdict = dashaidataset_created[1].split_dataset(
        dashaidataset_created[0], 0.7, 0.1, 0.2
    )

    train_rows = separate_datasetdict["train"].num_rows
    test_rows = separate_datasetdict["test"].num_rows
    validation_rows = separate_datasetdict["validation"].num_rows
    assert totals_rows == train_rows + test_rows + validation_rows


def split_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(datasetdict)
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, train_size=0.7, test_size=0.1, val_size=0.2
    )

    return separate_datasetdict


def test_save_to_disk_and_load():
    dataset = split_dataset()
    feature_names = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]
    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    dashai_datasetdict = load_dataset("tests/back/dataloaders/dashaidataset")
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    assert list((dashai_datasetdict["train"].features).keys()) == feature_names
    assert list((dashai_datasetdict["test"].features).keys()) == feature_names
    assert list((dashai_datasetdict["validation"].features).keys()) == feature_names


def test_divide_by_columns():
    inputs_columns = [
        "SepalLengthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species", "SepalWidthCm"]
    dataset = split_dataset()

    train_rows = dataset["train"].num_rows
    validation_rows = dataset["validation"].num_rows
    test_rows = dataset["test"].num_rows

    divided_dataset = divide_by_columns(dataset, inputs_columns, outputs_columns)

    assert divided_dataset["train"][0].shape == (train_rows, len(inputs_columns))
    assert divided_dataset["train"][1].shape == (train_rows, len(outputs_columns))
    assert divided_dataset["validation"][0].shape == (
        validation_rows,
        len(inputs_columns),
    )
    assert divided_dataset["validation"][1].shape == (
        validation_rows,
        len(outputs_columns),
    )
    assert divided_dataset["test"][0].shape == (test_rows, len(inputs_columns))
    assert divided_dataset["test"][1].shape == (test_rows, len(outputs_columns))
