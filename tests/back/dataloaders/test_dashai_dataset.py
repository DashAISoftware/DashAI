"""DashAI Dataset test suit module."""

# ruff: noqa: ERA001
import io
import pathlib
import shutil
from typing import List

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
    get_column_names_from_indexes,
    load_dataset,
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
    ("input_columns", "output_columns", "match"),
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
        "test_validate_inputs_outputs_throws_error_for_empty_input_columns",
        "test_validate_inputs_outputs_throws_error_for_wrong_size_inputs_output_columns",
        "test_validate_inputs_outputs_throws_error_for_wrong_input_columns",
    ],
)
def test_validate_inputs_outputs_errors(
    test_datasetdict: DatasetDict, input_columns, output_columns, match
):
    """Test several validate_inputs_outputs cases."""
    with pytest.raises(
        ValueError,
        match=match,
    ):
        validate_inputs_outputs(
            datasetdict=test_datasetdict,
            inputs=input_columns,
            outputs=output_columns,
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
        # test case 1 - try to change the type of an unexistant col.
        (
            {"unexistant_col": "Categorical"},
            ValueError,
            (
                r"Error while changing column types: column 'unexistant_col' does not "
                r"exist in dataset."
            ),
        ),
        # test case 2 - try to change a col to an incompatible type.
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
)
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


# TODO: Test invalid parameters (like split size of 0)
# TODO: Test split params, like seed, and shuffle.
# TODO: Test if it's possible to make a empty val split.
@pytest.mark.parametrize(
    ("train_size", "test_size", "val_size"),
    [
        (0.5, 0.25, 0.25),
        (0.7, 0.15, 0.15),
        (0.2, 0.75, 0.05),
    ],
)
def test_split_dataset(
    dashai_datasetdict: list,
    train_size: float,
    test_size: float,
    val_size: float,
):
    initial_dataset = dashai_datasetdict["train"]
    totals_rows = initial_dataset.num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=totals_rows,
        train_size=train_size,
        test_size=test_size,
        val_size=val_size,
    )

    assert totals_rows == len(train_indexes) + len(test_indexes) + len(val_indexes)

    # check empty splits intersections
    assert len(set(train_indexes).intersection(set(test_indexes))) == 0
    assert len(set(train_indexes).intersection(set(val_indexes))) == 0
    assert len(set(test_indexes).intersection(set(val_indexes))) == 0

    split_datasetdict = split_dataset(
        initial_dataset,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    assert "train" in split_datasetdict
    assert "test" in split_datasetdict
    assert "validation" in split_datasetdict

    train_rows = split_datasetdict["train"].num_rows
    test_rows = split_datasetdict["test"].num_rows
    validation_rows = split_datasetdict["validation"].num_rows

    assert totals_rows == train_rows + test_rows + validation_rows


# ----------------------------------------------------------------------------
# fixture: split dashai datasetdict


@pytest.fixture(name="split_dashai_datasetdict")
def split_dashai_datasetdict(test_datasetdict: DatasetDict):
    datasetdict = to_dashai_dataset(test_datasetdict)

    total_rows = len(datasetdict["train"])
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
    )
    split_dashai_datasetdict = split_dataset(
        datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return split_dashai_datasetdict


# ----------------------------------------------------------------------------
# test get_column_names_from_indexes


@pytest.mark.parametrize(
    ("col_indexes", "col_names"),
    [
        (
            [1],
            ["sepal length (cm)"],
        ),
        (
            [5],
            ["target"],
        ),
        (
            [1, 3, 4],
            [
                "sepal length (cm)",
                "petal length (cm)",
                "petal width (cm)",
            ],
        ),
        (
            [1, 2, 3, 4, 5],
            [
                "sepal length (cm)",
                "sepal width (cm)",
                "petal length (cm)",
                "petal width (cm)",
                "target",
            ],
        ),
        # TODO: check this case. I guess that i shouldn't work because
        # negative indexing.
        (
            [0],
            ["target"],
        ),
    ],
)
def test_get_column_names_from_indexes(
    split_dashai_datasetdict,
    col_indexes: list,
    col_names: list,
):
    feature_names = get_column_names_from_indexes(
        split_dashai_datasetdict,
        col_indexes,
    )

    assert feature_names == col_names


def test_parse_columns_indices_throws_error_for_wrong_index(split_dashai_datasetdict):
    input_columns_indices = [1, 3, 6]

    with pytest.raises(
        ValueError,
        match=(
            r"The list of indices can only contain elements within the amount "
            r"of columns. Index 6 is greater than the total of columns."
        ),
    ):
        get_column_names_from_indexes(split_dashai_datasetdict, input_columns_indices)


# ----------------------------------------------------------------------------
# test select columns


@pytest.mark.parametrize(
    ("input_columns", "output_columns"),
    [
        (
            ["sepal length (cm)"],
            ["target"],
        ),
        (
            ["sepal length (cm)", "petal length (cm)", "petal width (cm)"],
            ["target"],
        ),
        (
            [
                "sepal length (cm)",
                "petal length (cm)",
                "sepal width (cm)",
                "petal width (cm)",
            ],
            ["target"],
        ),
        (
            ["sepal length (cm)", "petal length (cm)"],
            ["target", "petal width (cm)"],
        ),
    ],
    ids=[
        "test_select_columns_one_in_one_out",
        "test_select_columns_three_x_one_y",
        "test_select_columns_four_x_one_y",
        "test_select_columns_two_x_two_y",
    ],
)
def test_select_columns(
    split_dashai_datasetdict, input_columns: List[str], output_columns: List[str]
):
    expected_train_rows = split_dashai_datasetdict["train"].num_rows
    expected_validation_rows = split_dashai_datasetdict["validation"].num_rows
    expected_test_rows = split_dashai_datasetdict["test"].num_rows

    x, y = select_columns(
        dataset=split_dashai_datasetdict,
        input_columns=input_columns,
        output_columns=output_columns,
    )
    # check cols
    assert x["train"].column_names == input_columns
    assert x["test"].column_names == input_columns
    assert x["validation"].column_names == input_columns

    assert y["train"].column_names == output_columns
    assert y["test"].column_names == output_columns
    assert y["validation"].column_names == output_columns

    # check n of rows
    assert x["train"].num_rows == expected_train_rows
    assert x["validation"].num_rows == expected_validation_rows
    assert x["test"].num_rows == expected_test_rows

    assert y["train"].num_rows == expected_train_rows
    assert y["validation"].num_rows == expected_validation_rows
    assert y["test"].num_rows == expected_test_rows


# ----------------------------------------------------------------------------
# test load and save dashai datasets


# TODO: Test save with just train split.
def test_save_to_disk_and_load(
    split_dashai_datasetdict,
    test_path: pathlib.Path,
):
    initial_num_cols = split_dashai_datasetdict.num_columns
    initial_num_rows = split_dashai_datasetdict.num_rows
    feature_names = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
        "target",
    ]
    save_dataset(
        datasetdict=split_dashai_datasetdict,
        path=str(test_path / "dataloaders/dashaidataset/load_and_save_test"),
    )

    loaded_datasetdict = load_dataset(
        dataset_path=str(test_path / "dataloaders/dashaidataset/load_and_save_test")
    )
    assert isinstance(loaded_datasetdict, datasets.DatasetDict)

    assert list((loaded_datasetdict["train"].features).keys()) == feature_names
    assert list((loaded_datasetdict["test"].features).keys()) == feature_names
    assert list((loaded_datasetdict["validation"].features).keys()) == feature_names

    loaded_num_cols = loaded_datasetdict.num_columns
    loaded_num_rows = loaded_datasetdict.num_rows

    assert initial_num_cols == loaded_num_cols
    assert initial_num_rows == loaded_num_rows


@pytest.fixture(name="split_dashai_datasetdict_two_class_cols")
def split_dashai_datasetdict_two_class_cols(test_datasetdict):
    """A split DashAIDataset with two target columns."""

    test_df = test_datasetdict["train"].to_pandas()
    test_df["target_2"] = test_df["target"].copy()
    new_datasetdict = datasets.DatasetDict(
        {"train": datasets.Dataset.from_pandas(test_df)}
    )

    datasetdict = to_dashai_dataset(new_datasetdict)

    total_rows = len(datasetdict["train"])
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
    )
    split_dashai_datasetdict = split_dataset(
        datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return split_dashai_datasetdict


# ----------------------------------------------------------------------------
# test update columns spec on disk


@pytest.mark.parametrize(
    ("dashai_datasetdict_fixture", "new_cols_specs"),
    [
        # test case 1 - change features to strings
        (
            "split_dashai_datasetdict",
            {
                "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "target": ColumnSpecItemParams(type="Value", dtype="string"),
            },
        ),
        # test case 2 - change target to classlabel
        (
            "split_dashai_datasetdict",
            {
                "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "target": ColumnSpecItemParams(type="ClassLabel", dtype="int64"),
            },
        ),
        # test case 3- change two cols to classlabel.
        (
            "split_dashai_datasetdict_two_class_cols",
            {
                "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
                "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
                "target": ColumnSpecItemParams(type="ClassLabel", dtype="int64"),
                "target_2": ColumnSpecItemParams(type="ClassLabel", dtype="int64"),
            },
        ),
    ],
    ids=[
        "test_update_columns_spec_change_value_types",
        "test_update_columns_spec_change_target_to_classlabel",
        "test_update_columns_spec_change_two_cols_to_classlabel",
    ],
)
def test_update_columns_spec_on_disk(
    dashai_datasetdict_fixture: str,
    new_cols_specs: dict,
    request: pytest.FixtureRequest,
    test_path: pathlib.Path,
):
    dashai_datasetdict = request.getfixturevalue(dashai_datasetdict_fixture)
    save_dataset(
        dashai_datasetdict,
        test_path / "dataloaders/dashaidataset/update_col_specs",
    )
    updated_dataset = update_columns_spec(
        str(test_path / "dataloaders/dashaidataset/update_col_specs"),
        columns=new_cols_specs,
    )

    updated_features = updated_dataset["train"].features
    assert list(updated_features.keys()) == list(new_cols_specs.keys())

    for col_name in new_cols_specs:
        assert new_cols_specs[col_name].type == updated_features[col_name]._type
        assert new_cols_specs[col_name].dtype == updated_features[col_name].dtype


# This test is not working with the current version of datasets.
# Check in the future if it is required or not with the new type definitions.
# def test_update_columns_spec_unsupported_input(
#     split_dashai_datasetdict,
#     test_path: pathlib.Path,
# ):
#     new_cols_specs = {
#         "sepal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
#         "sepal width (cm)": ColumnSpecItemParams(type="Value", dtype="bool"),
#         "petal length (cm)": ColumnSpecItemParams(type="Value", dtype="string"),
#         "petal width (cm)": ColumnSpecItemParams(type="Value", dtype="float64"),
#         "target": ColumnSpecItemParams(type="Value", dtype="string"),
#     }

#     save_dataset(
#         split_dashai_datasetdict,
#         str(test_path
#              / "dataloaders/dashaidataset/update_col_specs_unsupported_input"),
#     )
#     with pytest.raises(
#         ValueError,
#         match=("Error while trying to cast the columns"),
#     ):
#         update_columns_spec(
#             str(
#                 test_path
#                 / "dataloaders/dashaidataset/update_col_specs_unsupported_input"
#             ),
#             new_cols_specs,
#         )


@pytest.fixture(name="test_dataset_petal_width_dropped")
def prepare_iris_petal_width_dropped_dataset(test_datasetdict):
    new_dataset = DashAIDataset(
        datasets.Dataset.from_pandas(
            test_datasetdict["train"].to_pandas().drop(columns={"petal width (cm)"})
        ).data
    )

    return to_dashai_dataset(datasets.DatasetDict({"train": new_dataset}))


def test_remove_columns(
    test_datasetdict,
    test_dataset_petal_width_dropped,
):
    train_split: DashAIDataset = test_datasetdict["train"]
    train_dropped_split: DashAIDataset = test_dataset_petal_width_dropped["train"]

    # The datasets we use must be different
    assert train_split.column_names != train_dropped_split.column_names

    # Remove column from dataset
    train_split = train_split.remove_columns("petal width (cm)")

    assert "petal width (cm)" not in train_split
    assert len(train_split) == len(train_dropped_split)

    for column_name in train_dropped_split.column_names:
        assert train_split[column_name] == train_dropped_split[column_name]

    assert train_split.features == train_dropped_split.features


def test_update_splits_by_percentage(split_dashai_datasetdict):
    n = (
        len(split_dashai_datasetdict["train"])
        + len(split_dashai_datasetdict["test"])
        + len(split_dashai_datasetdict["validation"])
    )
    new_splits = {"train": 0.5, "test": 0.3, "validation": 0.2}

    new_dataset = update_dataset_splits(
        split_dashai_datasetdict,
        new_splits=new_splits,
        is_random=True,
    )

    assert len(new_dataset["train"]) == n * 0.5
    assert len(new_dataset["test"]) == n * 0.3
    assert len(new_dataset["validation"]) == n * 0.2


def test_update_splits_by_specific_rows(split_dashai_datasetdict):
    train_indexes = list(range(100))
    test_indexes = list(range(100, 130))
    val_indexes = list(range(130, 150))
    new_splits = {
        "train": train_indexes,
        "test": test_indexes,
        "validation": val_indexes,
    }

    new_dataset = update_dataset_splits(
        split_dashai_datasetdict,
        new_splits=new_splits,
        is_random=False,
    )

    assert len(new_dataset["train"]) == 100
    assert len(new_dataset["test"]) == 30
    assert len(new_dataset["validation"]) == 20
