import io
import pathlib
import shutil

import datasets
import pytest
from datasets import DatasetDict
from pyarrow.lib import ArrowInvalid
from sklearn.datasets import load_iris
from starlette.datastructures import UploadFile

from DashAI.back.api.api_v1.schemas.datasets_params import ColumnSpecItemParams
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    load_dataset,
    parse_columns_indices,
    save_dataset,
    select_columns,
    split_dataset,
    split_indexes,
    to_dashai_dataset,
    update_columns_spec,
    update_dataset_splits,
    validate_inputs_outputs,
)
from tests.back.test_datasets_generator import CSVTestDatasetGenerator


def _read_file_wrapper(dataset_path: pathlib.Path) -> UploadFile:
    """Read some file and simulate an upload by using UploadFile."""
    with open(dataset_path, "r") as file:
        loaded_bytes = file.read()
        bytes_buffer = io.BytesIO(bytes(loaded_bytes, encoding="utf8"))
        file = UploadFile(bytes_buffer)
    return file


@pytest.fixture(scope="module", autouse=True)
def _generate_test_dataset(test_datasets_path: pathlib.Path, random_state: int) -> None:
    """Generate the CSV test datasets."""

    df_iris = load_iris(return_X_y=False, as_frame=True)["frame"]  # type: ignore
    CSVTestDatasetGenerator(
        df=df_iris,
        dataset_name="iris",
        ouptut_path=test_datasets_path,
        random_state=random_state,
    )


@pytest.fixture(scope="module", autouse=True)
def _clean(test_path: pathlib.Path):
    """Clean the created datasets/dashai datasets created for test prupouses."""
    shutil.rmtree(test_path / "dataloaders/dashaidataset", ignore_errors=True)
    yield
    shutil.rmtree(test_path / "dataloaders/dashaidataset", ignore_errors=True)


@pytest.fixture(scope="module", name="test_datasetdict")
def load_test_datasetdict(test_datasets_path: pathlib.Path) -> DatasetDict:
    """Load a test datasetdict with the iris dataset."""
    test_dataset_path = test_datasets_path / "csv/iris/semicolon.csv"
    file = _read_file_wrapper(test_dataset_path)

    test_datasetdict = CSVDataLoader().load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/dataloaders",
        params={"separator": ";"},
    )

    return test_datasetdict


# ----------------------------------------------------------------------------
# test validate_inputs_outputs


@pytest.mark.parametrize(
    ("inputs_columns", "outputs_columns", "match"),
    [
        # test case 1 - empty input cols
        (
            [],
            ["target"],
            r"Inputs and outputs columns lists to validate must not be empty",
        ),
        # test case 2 - extra output cols
        (
            [
                "sepal length (cm)",
                "sepal width (cm)",
                "petal length (cm)",
                "petal width (cm)",
            ],
            ["target", "sepal width (cm)"],
            (
                r"Inputs and outputs cannot have more elements than names. Number of "
                r"inputs: 4, number of outputs: 2, number of names: 5. "
            ),
        ),
        # test case 3 - non existant input col
        (
            [
                "unexistant_col",
                "sepal width (cm)",
                "petal length (cm)",
                "petal width (cm)",
            ],
            ["target"],
            (
                r"Inputs and outputs can only contain elements that exist in names. "
                r"Extra elements: unexistant_col"
            ),
        ),
    ],
    ids=[
        "test_validate_inputs_outputs_throws_error_for_empty_inputs_columns",
        "test_validate_inputs_outputs_throws_error_for_wrong_size_inputs_outputs_columns",
        "test_validate_inputs_outputs_throws_error_for_wrong_input_columns",
    ],
)
def test_validate_inputs_outputs_errors(
    test_datasetdict: DatasetDict, inputs_columns, outputs_columns, match
):
    """Test several validate_inputs_outputs cases."""
    with pytest.raises(
        ValueError,
        match=match,
    ):
        validate_inputs_outputs(
            datasetdict=test_datasetdict,
            inputs=inputs_columns,
            outputs=outputs_columns,
        )


@pytest.fixture(name="dashai_datasetdict")
def load_dashai_dataset(test_datasetdict):
    """Create the test dashai datasetdict."""
    # TODO: Test with a dataset with splits.
    loaded_dashai_datasetdict = to_dashai_dataset(test_datasetdict)
    return loaded_dashai_datasetdict


# ----------------------------------------------------------------------------
# test dataset sample


@pytest.mark.parametrize(
    ("method", "n_samples"),
    [
        ("head", 1),
        ("head", 10),
        ("head", 50),
        ("tail", 1),
        ("tail", 10),
        ("tail", 50),
        ("random", 1),
        ("random", 10),
        ("random", 50),
    ],
    ids=[
        "test_sample_dashaidataset_head_1",
        "test_sample_dashaidataset_head_10",
        "test_sample_dashaidataset_head_50",
        "test_sample_dashaidataset_tail_1",
        "test_sample_dashaidataset_tail_10",
        "test_sample_dashaidataset_tail_50",
        "test_sample_dashaidataset_random_1",
        "test_sample_dashaidataset_random_10",
        "test_sample_dashaidataset_random_50",
    ],
)
def test_sample_dashaidataset(dashai_datasetdict: list, method: str, n_samples: int):
    for split in dashai_datasetdict:
        dataset = dashai_datasetdict[split]

        sample = dataset.sample(n=n_samples, method=method)
        values = list(sample.values())
        len_sample = len(values[0])

        assert sample.keys() == dataset.features.keys()
        assert isinstance(sample, dict)
        assert all(len(item) == len_sample for item in values)

        if method == "head":
            assert sample == dataset[:n_samples]

        elif method == "tail":
            assert sample == dataset[-n_samples:]

        elif method == "random":
            for index in list(range(len_sample)):
                one_sample = {key: None for key in sample}
                for key in one_sample:
                    one_sample[key] = sample[key][index]
                assert any(one_sample == data for data in dataset)


# ----------------------------------------------------------------------------
# test change_columns_type


@pytest.mark.parametrize(
    ("col_types", "expected_exception", "match"),
    [
        # case 1 - try to change the type of an unexistant col.
        (
            {"unexistant_col": "Categorical"},
            ValueError,
            (
                r"Error while changing column types: column 'unexistant_col' does not "
                r"exist in dataset."
            ),
        ),
        # case 2 - try to change a col to an incompatible type.
        (
            {"sepal length (cm)": "Categorical"},
            ArrowInvalid,
            r"Float value .{2,5} was truncated converting to int64",
        ),
    ],
    ids=[
        "test_change_columns_type_raises_error_for_unexistant_col",
        "test_change_columns_type_raises_error_for_incompatible_type_casting",
    ],
)  # Error while changing column types: column 'unexistant_col' does not exist in dataset.
def test_change_columns_type_errors(
    dashai_datasetdict: list, col_types, expected_exception, match
):
    for split in dashai_datasetdict:
        with pytest.raises(expected_exception, match=match):
            dashai_datasetdict[split].change_columns_type(col_types)


def test_dashai_datasetdict_change_columns_type_target_col_as_cat(
    dashai_datasetdict: DatasetDict,
):
    """Test target column casting to a Categorical (ClassLabel) type."""

    for split in dashai_datasetdict.values():
        original_features = split.features.copy()

        split = split.change_columns_type({"target": "Categorical"})
        new_features = split.features

        assert len(original_features) == len(new_features)

        assert original_features["target"].dtype == "int64"
        assert new_features["target"].dtype == "int64"

        # check the new types.
        assert isinstance(original_features["target"], datasets.features.Value)
        assert isinstance(new_features["target"], datasets.features.ClassLabel)

        # check that the rest of the features remain unmodified.
        for feature_name in original_features:
            if feature_name != "target":
                assert isinstance(
                    original_features[feature_name], datasets.features.Value
                )
                assert isinstance(new_features[feature_name], datasets.features.Value)
                assert original_features[feature_name] == new_features[feature_name]


# ----------------------------------------------------------------------------
# test split dataset


def test_split_dataset(dashai_datasetdict: list):
    totals_rows = dashai_datasetdict["train"].num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=totals_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    separate_datasetdict = split_dataset(
        dashai_datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    train_rows = separate_datasetdict["train"].num_rows
    test_rows = separate_datasetdict["test"].num_rows
    validation_rows = separate_datasetdict["validation"].num_rows
    assert totals_rows == train_rows + test_rows + validation_rows


@pytest.fixture(name="split_dashai_datasetdict")
def split_iris_dataset(test_datasetdict: DatasetDict):
    datasetdict = to_dashai_dataset(test_datasetdict)

    total_rows = len(datasetdict["train"])
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_dashai_datasetdict = split_dataset(
        datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return split_dashai_datasetdict


def test_save_to_disk_and_load(split_dashai_datasetdict):
    feature_names = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
        "target",
    ]
    save_dataset(split_dashai_datasetdict, "tests/back/dataloaders/dashaidataset")
    dashai_datasetdict = load_dataset("tests/back/dataloaders/dashaidataset")
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    assert list((dashai_datasetdict["train"].features).keys()) == feature_names
    assert list((dashai_datasetdict["test"].features).keys()) == feature_names
    assert list((dashai_datasetdict["validation"].features).keys()) == feature_names


def test_parse_columns_indices(split_dashai_datasetdict):
    input_columns_indices = [1, 3, 4]
    input_columns_names = ["sepal length (cm)", "petal length (cm)", "petal width (cm)"]
    feature_names1 = parse_columns_indices(
        split_dashai_datasetdict, input_columns_indices
    )

    assert feature_names1 == input_columns_names


def test_parse_columns_indices_wrong_index(split_dashai_datasetdict):
    input_columns_indices = [1, 3, 6]

    with pytest.raises(
        ValueError,
        match=(
            r"The list of indices can only contain elements within the amount "
            r"of columns. Index 6 is greater than the total of columns."
        ),
    ):
        parse_columns_indices(split_dashai_datasetdict, input_columns_indices)


def test_select_columns(split_dashai_datasetdict):
    inputs_columns = [
        "sepal length (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    outputs_columns = ["target"]

    train_rows = split_dashai_datasetdict["train"].num_rows
    validation_rows = split_dashai_datasetdict["validation"].num_rows
    test_rows = split_dashai_datasetdict["test"].num_rows

    x, y = select_columns(split_dashai_datasetdict, inputs_columns, outputs_columns)

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


def test_update_columns_spec_valid(split_dashai_datasetdict):
    modify_data = {
        "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "target": ColumnSpecItemParams(type="Value", dtype="string"),
    }

    save_dataset(split_dashai_datasetdict, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
        "target",
    ]
    assert new_features["sepal length (cm)"]._type == "Value"
    assert new_features["sepal length (cm)"].dtype == "string"
    assert new_features["sepal width (cm)"]._type == "Value"
    assert new_features["sepal width (cm)"].dtype == "float64"
    assert new_features["petal length (cm)"]._type == "Value"
    assert new_features["petal length (cm)"].dtype == "string"
    assert new_features["petal width (cm)"]._type == "Value"
    assert new_features["petal width (cm)"].dtype == "float64"
    assert new_features["target"]._type == "Value"
    assert new_features["target"].dtype == "string"


def test_update_columns_spec_unsoported_input(split_dashai_datasetdict):
    modify_data = {
        "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="bool"),
        "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "target": ColumnSpecItemParams(type="Value", dtype="bool"),
    }

    save_dataset(split_dashai_datasetdict, "tests/back/dataloaders/dashaidataset")
    with pytest.raises(
        ValueError,
        match=("Error while trying to cast the columns"),
    ):
        update_columns_spec("tests/back/dataloaders/dashaidataset", modify_data)

    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)


def test_update_columns_spec_one_class_column(split_dashai_datasetdict):
    modify_data = {
        "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "target": ColumnSpecItemParams(type="ClassLabel", dtype=""),
    }

    save_dataset(split_dashai_datasetdict, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
        "target",
    ]
    assert new_features["sepal length (cm)"]._type == "Value"
    assert new_features["sepal length (cm)"].dtype == "string"
    assert new_features["sepal width (cm)"]._type == "Value"
    assert new_features["sepal width (cm)"].dtype == "float64"
    assert new_features["petal length (cm)"]._type == "Value"
    assert new_features["petal length (cm)"].dtype == "string"
    assert new_features["petal width (cm)"]._type == "Value"
    assert new_features["petal width (cm)"].dtype == "float64"
    assert new_features["target"]._type == "ClassLabel"


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

    total_rows = len(datasetdict["train"])
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    separate_datasetdict = split_dataset(
        datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return separate_datasetdict


def test_update_columns_spec_multiple_class_columns():
    dataset = split_dataset_with_two_classes()
    modify_data = {
        "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
        "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
        "target": ColumnSpecItemParams(type="ClassLabel", dtype=""),
        "Species-2": ColumnSpecItemParams(type="ClassLabel", dtype=""),
    }

    save_dataset(dataset, "tests/back/dataloaders/dashaidataset")
    updated_dataset = update_columns_spec(
        "tests/back/dataloaders/dashaidataset", modify_data
    )
    shutil.rmtree("tests/back/dataloaders/dashaidataset", ignore_errors=True)

    new_features = updated_dataset["train"].features
    assert list(new_features.keys()) == [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
        "target",
        "Species-2",
    ]
    assert new_features["sepal length (cm)"]._type == "Value"
    assert new_features["sepal length (cm)"].dtype == "string"
    assert new_features["sepal width (cm)"]._type == "Value"
    assert new_features["sepal width (cm)"].dtype == "float64"
    assert new_features["petal length (cm)"]._type == "Value"
    assert new_features["petal length (cm)"].dtype == "string"
    assert new_features["petal width (cm)"]._type == "Value"
    assert new_features["petal width (cm)"].dtype == "float64"
    assert new_features["target"]._type == "ClassLabel"
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
    train_split.remove_columns("petal width (cm)")
    assert len(train_split) == len(train_dropped_split)
    for column_name in train_split.column_names:
        assert train_split[column_name] == train_dropped_split[column_name]
    assert train_split.features == train_dropped_split.features


def test_update_splits_by_percentage():
    iris_dataset = split_iris_dataset()
    n = (
        len(iris_dataset["train"])
        + len(iris_dataset["test"])
        + len(iris_dataset["validation"])
    )
    new_splits = {"train": 0.5, "test": 0.3, "validation": 0.2}

    new_dataset = update_dataset_splits(
        iris_dataset, new_splits=new_splits, is_random=True
    )

    assert len(new_dataset["train"]) == n * 0.5
    assert len(new_dataset["test"]) == n * 0.3
    assert len(new_dataset["validation"]) == n * 0.2


def test_update_splits_by_specific_rows():
    iris_dataset = split_iris_dataset()
    train_indexes = list(range(100))
    test_indexes = list(range(100, 130))
    val_indexes = list(range(130, 150))
    new_splits = {
        "train": train_indexes,
        "test": test_indexes,
        "validation": val_indexes,
    }

    new_dataset = update_dataset_splits(
        iris_dataset, new_splits=new_splits, is_random=False
    )

    assert len(new_dataset["train"]) == 100
    assert len(new_dataset["test"]) == 30
    assert len(new_dataset["validation"]) == 20
