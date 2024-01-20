import io
import shutil

import pytest
from datasets import ClassLabel, DatasetDict
from pyarrow.lib import ArrowInvalid
from starlette.datastructures import UploadFile

from DashAI.back.api.api_v1.schemas.datasets_params import ColumnSpecItemParams
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    load_dataset,
    parse_columns_indices,
    save_dataset,
    select_columns,
    update_columns_spec,
    validate_inputs_outputs,
)
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset


@pytest.fixture(scope="module", autouse=True)
def clean():
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)
    yield
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)
    return True


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


def test_validate_empty_inputs_outputs_columns(dataset_created: DatasetDict):
    inputs_colums = []
    outputs_columns = ["Species"]

    with pytest.raises(
        ValueError,
        match="Inputs and outputs columns lists to validate must not be empty",
    ):
        validate_inputs_outputs(dataset_created, inputs_colums, outputs_columns)


def test_validate_wrong_size_inputs_outputs_columns(dataset_created: DatasetDict):
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


def test_validate_wrong_name_outputs_columns(dataset_created: DatasetDict):
    inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    with pytest.raises(
        ValueError,
        match=(
            r"Inputs and outputs can only contain elements that exist in names. "
            r"Extra elements: Sepal"
        ),
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


def test_parse_columns_indices():
    input_columns_indices = [1, 3, 4]
    input_columns_names = ["SepalLengthCm", "PetalLengthCm", "PetalWidthCm"]

    dataset = split_dataset()
    feature_names1 = parse_columns_indices(dataset, input_columns_indices)

    assert feature_names1 == input_columns_names


def test_parse_columns_indices_wrong_index():
    input_columns_indices = [1, 3, 6]

    dataset = split_dataset()

    with pytest.raises(
        ValueError,
        match=(
            r"The list of indices can only contain elements within the amount "
            r"of columns. Index 6 is greater than the total of columns."
        ),
    ):
        parse_columns_indices(dataset, input_columns_indices)


def test_select_columns():
    inputs_columns = [
        "SepalLengthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species"]
    dataset = split_dataset()

    train_rows = dataset["train"].num_rows
    validation_rows = dataset["validation"].num_rows
    test_rows = dataset["test"].num_rows

    x, y = select_columns(dataset, inputs_columns, outputs_columns)

    assert x["train"].shape == (train_rows, len(inputs_columns))
    assert x["validation"].shape == (
        validation_rows,
        len(inputs_columns),
    )
    assert x["test"].shape == (test_rows, len(inputs_columns))
    assert y["train"].shape == (train_rows, len(outputs_columns))
    assert y["validation"].shape == (
        validation_rows,
        len(outputs_columns),
    )
    assert y["test"].shape == (test_rows, len(outputs_columns))


def test_update_columns_spec_valid():
    dataset = split_dataset()
    modify_data = {
        "SepalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "SepalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "PetalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "PetalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "Species": ColumnSpecItemParams(type="Value", dtype="string"),
    }

    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]
    assert new_features["SepalLengthCm"]._type == "Value"
    assert new_features["SepalLengthCm"].dtype == "string"
    assert new_features["SepalWidthCm"]._type == "Value"
    assert new_features["SepalWidthCm"].dtype == "float64"
    assert new_features["PetalLengthCm"]._type == "Value"
    assert new_features["PetalLengthCm"].dtype == "string"
    assert new_features["PetalWidthCm"]._type == "Value"
    assert new_features["PetalWidthCm"].dtype == "float64"
    assert new_features["Species"]._type == "Value"
    assert new_features["Species"].dtype == "string"


def test_update_columns_spec_unsoported_input():
    dataset = split_dataset()
    modify_data = {
        "SepalLengthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "SepalWidthCm": ColumnSpecItemParams(type="Value", dtype="bool"),
        "PetalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "PetalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "Species": ColumnSpecItemParams(type="Value", dtype="bool"),
    }

    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    with pytest.raises(
        ValueError,
        match=("Error while trying to cast the columns"),
    ):
        update_columns_spec("tests/back/dataloaders/dashaidataset", modify_data)

    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)


def test_update_columns_spec_one_class_column():
    dataset = split_dataset()
    modify_data = {
        "SepalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "SepalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "PetalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "PetalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "Species": ColumnSpecItemParams(type="ClassLabel", dtype=""),
    }

    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]
    assert new_features["SepalLengthCm"]._type == "Value"
    assert new_features["SepalLengthCm"].dtype == "string"
    assert new_features["SepalWidthCm"]._type == "Value"
    assert new_features["SepalWidthCm"].dtype == "float64"
    assert new_features["PetalLengthCm"]._type == "Value"
    assert new_features["PetalLengthCm"].dtype == "string"
    assert new_features["PetalWidthCm"]._type == "Value"
    assert new_features["PetalWidthCm"].dtype == "float64"
    assert new_features["Species"]._type == "ClassLabel"


def split_dataset_with_two_classes():
    test_dataset_path = "tests/back/dataloaders/iris_species_twice.csv"
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


def test_update_columns_spec_multiple_class_columns():
    dataset = split_dataset_with_two_classes()
    modify_data = {
        "SepalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "SepalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "PetalLengthCm": ColumnSpecItemParams(type="Value", dtype="string"),
        "PetalWidthCm": ColumnSpecItemParams(type="Value", dtype="float64"),
        "Species": ColumnSpecItemParams(type="ClassLabel", dtype=""),
        "Species-2": ColumnSpecItemParams(type="ClassLabel", dtype=""),
    }

    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
        "Species-2",
    ]
    assert new_features["SepalLengthCm"]._type == "Value"
    assert new_features["SepalLengthCm"].dtype == "string"
    assert new_features["SepalWidthCm"]._type == "Value"
    assert new_features["SepalWidthCm"].dtype == "float64"
    assert new_features["PetalLengthCm"]._type == "Value"
    assert new_features["PetalLengthCm"].dtype == "string"
    assert new_features["PetalWidthCm"]._type == "Value"
    assert new_features["PetalWidthCm"].dtype == "float64"
    assert new_features["Species"]._type == "ClassLabel"
    assert new_features["Species-2"]._type == "ClassLabel"


@pytest.fixture(name="iris_dataset")
def prepare_iris_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
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
    test_dataset_path = "tests/back/dataloaders/iris_petal_width_dropped.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(datasetdict)

    return datasetdict


def test_remove_columns(
    iris_dataset: DatasetDict, iris_dataset_petal_width_dropped: DatasetDict
):
    assert type(iris_dataset["train"]) is DashAIDataset
    assert type(iris_dataset_petal_width_dropped["train"]) is DashAIDataset
    train_split: DashAIDataset = iris_dataset["train"]
    train_dropped_split: DashAIDataset = iris_dataset_petal_width_dropped["train"]
    # The datasets we use must be different
    assert id(train_split) != id(train_dropped_split)
    # Remove column from dataset
    train_split.remove_columns("PetalWidthCm")
    assert len(train_split) == len(train_dropped_split)
    for column_name in train_split.column_names:
        assert train_split[column_name] == train_dropped_split[column_name]
    assert train_split.features == train_dropped_split.features
