"""DashAI Dataset implementation."""

import json
import os
import pathlib
from copy import deepcopy
from typing import Dict, List, Literal, Tuple, Union

import numpy as np
import pyarrow as pa
from beartype import beartype
from datasets import (
    ClassLabel,
    Dataset,
    DatasetDict,
    Value,
    concatenate_datasets,
    load_from_disk,
)
from datasets.table import Table
from sklearn.model_selection import train_test_split

from DashAI.back.types.categorical import Categorical
from DashAI.back.types.one_hot_encode_type import OneHotEncodeType


class DashAIDataset(Dataset):
    """DashAI dataset wrapper for Huggingface datasets with extra metadata."""

    @beartype
    def __init__(
        self,
        table: Table,
        *args,
        **kwargs,
    ):
        """Initialize a new instance of a DashAI dataset.

        Parameters
        ----------
        table : Table
            Arrow table from which the dataset will be created
        """
        super().__init__(table, *args, **kwargs)

    @beartype
    def cast(self, *args, **kwargs) -> "DashAIDataset":
        """Override of the cast method to leave it in DashAI dataset format.

        Returns
        -------
        DatasetDashAI
            Dataset after cast
        """
        ds = super().cast(*args, **kwargs)
        return DashAIDataset(ds._data)

    @beartype
    def save_to_disk(self, dataset_path: str) -> None:
        """Saves a dataset to a dataset directory, or in a filesystem.

        Overwrite the original method to include the input and output columns.

        Parameters
        ----------
        dataset_path : str
            path where the dataset will be stored
        """
        super().save_to_disk(dataset_path)

    @beartype
    def change_columns_type(self, column_types: Dict[str, str]) -> "DashAIDataset":
        """Change the type of some columns.

        Note: this is a temporal method, and it will probably will delete in the future.

        Parameters
        ----------
        column_types : Dict[str, str]
            dictionary whose keys are the names of the columns to be changed and the
            values the new types.

        Returns
        -------
        DashAIDataset
            The dataset after columns type changes.
        """
        if not isinstance(column_types, dict):
            raise TypeError(f"types should be a dict, got {type(column_types)}")

        for column in column_types:
            if column in self.column_names:
                pass
            else:
                raise ValueError(
                    f"Error while changing column types: column '{column}' does not "
                    "exist in dataset."
                )
        new_features = self.features.copy()
        for column in column_types:
            if column_types[column] == "Categorical":
                names = list(set(self[column]))
                new_features[column] = ClassLabel(names=names)
            elif column_types[column] == "Numerical":
                new_features[column] = Value("float32")
        dataset = self.cast(new_features)
        return dataset

    @beartype
    def remove_columns(self, column_names: Union[str, List[str]]) -> "DashAIDataset":
        """Remove one or several column(s) in the dataset and the features
        associated to them.

        Parameters
        ----------
        column_names : Union[str, List[str]]
            Name, or list of names of columns to be removed.

        Returns
        -------
        DashAIDataset
            The dataset after columns removal.
        """
        if isinstance(column_names, str):
            column_names = [column_names]

        # Remove column from features
        modified_dataset = super().remove_columns(column_names)
        # Update self with modified dataset attributes
        self.__dict__.update(modified_dataset.__dict__)

        return self

    @beartype
    def sample(
        self,
        n: int = 1,
        method: Literal["head", "tail", "random"] = "head",
        seed: Union[int, None] = None,
    ) -> Dict[str, List]:
        """Return sample rows from dataset.

        Parameters
        ----------
        n : int
            number of samples to return.
        method: Literal[str]
            method for selecting samples. Possible values are: 'head' to
            select the first n samples, 'tail' to select the last n samples
            and 'random' to select n random samples.
        seed : int, optional
            seed for random number generator when using 'random' method.

        Returns
        -------
        Dict
            A dictionary with selected samples.
        """
        if n > len(self):
            raise ValueError(
                "Number of samples must be less than or equal to the length "
                f"of the dataset. Number of samples: {n}, "
                f"dataset length: {len(self)}"
            )

        if method == "random":
            rng = np.random.default_rng(seed=seed)
            indexes = rng.integers(low=0, high=(len(self) - 1), size=n)
            sample = self.select(indexes).to_dict()

        elif method == "head":
            sample = self[:n]

        elif method == "tail":
            sample = self[-n:]

        return sample

    def class_encode_column(
        self, column: str, include_nulls: bool = False
    ) -> "DashAIDataset":
        """Encode the given column to a categorical column.

        Parameters
        ----------
        column : str
            Name of the column to encode
        include_nulls : bool, optional
            Whether to include null values in the encoding. If `True`,
            the null values will be encoded as the `"None"` class label.

        Returns
        -------
        DashAIDataset
            DashAI Dataset with the column encoded
        """
        dataset = super().class_encode_column(column, include_nulls)
        feats = dataset.features.copy()
        feats[column] = Categorical(feats[column].names)
        return DashAIDataset(dataset.data).cast(feats)

    def one_hot_encode_column(
        self, column: str, delete_original_column: bool = True
    ) -> "DashAIDataset":
        """Encode the given categorical column to a one hot encoding.

        Parameters
        ----------
        column : str
            Column to encode. It must be a categorical column.
        delete_original_column : bool, optional
            whether the original column is deleted, by default True
        """
        if column not in self.column_names:
            raise ValueError(f"Column '{column}' is not in the dataset.")
        if not isinstance(self.features[column], ClassLabel):
            raise ValueError("Only categorical columns can be one hot encoded.")

        categorical_feat: Categorical = self.features[column]
        categories = categorical_feat.names
        dataset = deepcopy(self)
        for category in categories:
            column_data = np.zeros(self.num_rows, dtype=np.int64)
            column_name = f"{column}_{category}"
            dataset = dataset.add_column(column_name, column_data)
            dataset = dataset.cast(
                column_name,
                OneHotEncodeType(
                    categorical_feature=categorical_feat, category=category
                ),
            )

        def one_hot_encode(example):
            col_name = f"{column}_{categories[example[column]]}"
            example[col_name] = 1
            return example

        dataset = dataset.map(one_hot_encode)
        if delete_original_column:
            dataset = dataset.remove_columns(column)

        return dataset


@beartype
def load_dataset(dataset_path: str) -> DatasetDict:
    """Load a DashAI dataset from its path.

         This process cast each split into a DashAIdataset object.

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.

    Returns
    -------
    DatasetDict
        The loaded dataset.
    """
    dataset = load_from_disk(dataset_path=dataset_path)

    for split in dataset:
        dataset[split] = DashAIDataset(dataset[split].data)

    return dataset


@beartype
def save_dataset(datasetdict: DatasetDict, path: Union[str, pathlib.Path]) -> None:
    """Save the datasetdict with dashaidatasets inside.

    Parameters
    ----------
    datasetdict : DatasetDict
        The dataset to be saved.

    datasetdict_path : str
        Path where the dtaaset will be stored.

    """
    splits = []
    for split in datasetdict:
        splits.append(split)
        datasetdict[split].save_to_disk(f"{path}/{split}")

    with open(
        os.path.join(path, "dataset_dict.json"), "w", encoding="utf-8"
    ) as datasetdict_info_file:
        data = {"splits": splits}
        json.dump(
            data,
            datasetdict_info_file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )


@beartype
def check_split_values(
    train_size: float,
    test_size: float,
    val_size: float,
) -> None:
    if train_size < 0 or train_size > 1:
        raise ValueError(
            "train_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )
    if test_size < 0 or test_size > 1:
        raise ValueError(
            "test_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )
    if val_size < 0 or val_size > 1:
        raise ValueError(
            "val_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )


@beartype
def split_indexes(
    total_rows: int,
    train_size: float,
    test_size: float,
    val_size: float,
    seed: Union[int, None] = None,
    shuffle: bool = True,
) -> Tuple[List, List, List]:
    """Generate lists with train, test and validation indexes.

    The algorithm for splitting the dataset is as follows:

    1. The dataset is divided into a training and a test-validation split
        (sum of test_size and val_size).
    2. The test and validation set is generated from the test-validation set,
        where the size of the test-validation set is now considered to be 100%.
        Therefore, the sizes of the test and validation sets will now be
        calculated as 100%, i.e. as val_size/(test_size+val_size) and
        test_size/(test_size+val_size) respectively.

    Example:

    If we split a dataset into 0.8 training, a 0.1 test, and a 0.1 validation,
    in the first process we split the training data with 80% of the data, and
    the test-validation data with the remaining 20%; and then in the second
    process we split this 20% into 50% test and 50% validation.

    Parameters
    ----------
    total_rows : int
        Size of the Dataset.
    train_size : float
        Proportion of the dataset for train split (in 0-1).
    test_size : float
        Proportion of the dataset for test split (in 0-1).
    val_size : float
        Proportion of the dataset for validation split (in 0-1).
    seed : Union[int, None], optional
        Set seed to control to enable replicability, by default None
    shuffle : bool, optional
        If True, the data will be shuffled when splitting the dataset,
        by default True.

    Returns
    -------
    Tuple[List, List, List]
        Train, Test and Validation indexes.
    """

    # Generate shuffled indexes
    np.random.seed(seed)
    indexes = np.arange(total_rows)

    test_val = test_size + val_size
    val_proportion = test_size / test_val
    train_indexes, test_val_indexes = train_test_split(
        indexes,
        train_size=train_size,
        random_state=seed,
        shuffle=shuffle,
    )
    test_indexes, val_indexes = train_test_split(
        test_val_indexes,
        train_size=val_proportion,
        random_state=seed,
        shuffle=shuffle,
    )
    return list(train_indexes), list(test_indexes), list(val_indexes)


@beartype
def split_dataset(
    dataset: Dataset,
    train_indexes: List,
    test_indexes: List,
    val_indexes: List,
) -> DatasetDict:
    """Split the dataset in train, test and validation subsets.

    Parameters
    ----------
    dataset : DatasetDict
        A HuggingFace DatasetDict containing the dataset to be split.
    train_indexes : List
        Train split indexes.
    test_indexes : List
        Test split indexes.
    val_indexes : List
        Validation split indexes.


    Returns
    -------
    DatasetDict
        The split dataset.
    """

    # Get the number of records
    n = len(dataset)

    # Convert the indexes into boolean masks
    train_mask = np.isin(np.arange(n), train_indexes)
    test_mask = np.isin(np.arange(n), test_indexes)
    val_mask = np.isin(np.arange(n), val_indexes)

    # Get the underlying table
    table = dataset.data

    # Create separate tables for each split
    train_table = table.filter(pa.array(train_mask))
    test_table = table.filter(pa.array(test_mask))
    val_table = table.filter(pa.array(val_mask))

    separate_dataset_dict = DatasetDict(
        {
            "train": Dataset(train_table),
            "test": Dataset(test_table),
            "validation": Dataset(val_table),
        }
    )

    dataset = to_dashai_dataset(separate_dataset_dict)
    return dataset


def to_dashai_dataset(dataset: DatasetDict) -> DatasetDict:
    """
    Convert all datasets within the DatasetDict to DashAIDataset.

    Returns
    -------
    DatasetDict:
        Datasetdict with datasets converted to DashAIDataset.
    """
    for key in dataset:
        dataset[key] = DashAIDataset(dataset[key].data)
    return dataset


@beartype
def validate_inputs_outputs(
    datasetdict: DatasetDict,
    inputs: List[str],
    outputs: List[str],
) -> None:
    """Validate the columns to be chosen as input and output.
    The algorithm considers those that already exist in the dataset.

    Parameters
    ----------
    names : List[str]
        Dataset column names.
    inputs : List[str]
        List of input column names.
    outputs : List[str]
        List of output column names.
    """
    dataset_features = list((datasetdict["train"].features).keys())
    if len(inputs) == 0 or len(outputs) == 0:
        raise ValueError(
            "Inputs and outputs columns lists to validate must not be empty"
        )
    if len(inputs) + len(outputs) > len(dataset_features):
        raise ValueError(
            "Inputs and outputs cannot have more elements than names. "
            f"Number of inputs: {len(inputs)}, "
            f"number of outputs: {len(outputs)}, "
            f"number of names: {len(dataset_features)}. "
        )
        # Validate that inputs and outputs only contain elements that exist in names
    if not set(dataset_features).issuperset(set(inputs + outputs)):
        raise ValueError(
            f"Inputs and outputs can only contain elements that exist in names. "
            f"Extra elements: "
            f"{', '.join(set(inputs + outputs).difference(set(dataset_features)))}"
        )


@beartype
def parse_columns_indices(datasetdict: DatasetDict, indices: List[int]) -> List[str]:
    """Returns the column labes of the dataset that correspond to the indices

    Args:
        dataset_path (str): Path where the dataset is stored
        indices (List[int]): List with the indices of the columns

    Returns:
        List[str]: List with the labels of the columns
    """
    dataset_features = list((datasetdict["train"].features).keys())
    names_list = []
    for index in indices:
        if index > len(dataset_features):
            raise ValueError(
                f"The list of indices can only contain elements within"
                f" the amount of columns. "
                f"Index {index} is greater than the total of columns."
            )
        names_list.append(dataset_features[index - 1])
    return names_list


@beartype
def select_columns(
    dataset: DatasetDict, input_columns: List[str], output_columns: List[str]
) -> Tuple[DatasetDict, DatasetDict]:
    """Divide the dataset into a dataset with only the input columns in it
    and other dataset only with the output columns

    Parameters
    ----------
    dataset : DatasetDict
        Dataset to divide
    input_columns : List[str]
        List with the input columns labels
    output_columns : List[str]
        List with the output columns labels

    Returns
    -------
    Tuple[DatasetDict, DatasetDict]
        Tuple with the separated DatasetDicts x and y
    """
    input_columns_dataset = DatasetDict()
    output_columns_dataset = DatasetDict()
    for split in dataset:
        input_columns_dataset[split] = dataset[split].select_columns(input_columns)
        output_columns_dataset[split] = dataset[split].select_columns(output_columns)
    return (input_columns_dataset, output_columns_dataset)


@beartype
def get_columns_spec(dataset_path: str) -> Dict[str, Dict]:
    """Return the column with their respective types

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.

    Returns
    -------
    Dict
        Dict with the columns and types
    """
    dataset = load_dataset(dataset_path=dataset_path)
    dataset_features = dataset["train"].features
    column_types = {}
    for column in dataset_features:
        if dataset_features[column]._type == "Value":
            column_types[column] = {
                "type": "Value",
                "dtype": dataset_features[column].dtype,
            }
        elif dataset_features[column]._type == "ClassLabel":
            column_types[column] = {
                "type": "Classlabel",
                "dtype": "",
            }
    return column_types


@beartype
def update_columns_spec(dataset_path: str, columns: Dict) -> DatasetDict:
    """Return the column with their respective types

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.
    columns : Dict
        Dict with columns and types to change
    Returns
    -------
    Dict
        Dict with the columns and types
    """
    if not isinstance(columns, dict):
        raise TypeError(f"types should be a dict, got {type(columns)}")

    # Load the dataset from where its stored
    dataset_dict = load_from_disk(dataset_path=dataset_path)
    for split in dataset_dict:
        # Copy the features with the columns ans types
        new_features = dataset_dict[split].features
        for column in columns:
            if columns[column].type == "ClassLabel":
                names = list(set(dataset_dict[split][column]))
                new_features[column] = ClassLabel(names=names)
            elif columns[column].type == "Value":
                new_features[column] = Value(columns[column].dtype)
        # Cast the column types with the changes
        try:
            dataset_dict[split] = dataset_dict[split].cast(new_features)
        except ValueError as e:
            raise ValueError("Error while trying to cast the columns") from e
    return dataset_dict


def get_dataset_info(dataset_path: str) -> object:
    """Return the info of the dataset with the number of rows,
    number of columns and splits size.

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.

    Returns
    -------
    object
        Dictionary with the information of the dataset
    """
    dataset = load_dataset(dataset_path=dataset_path)
    total_rows = sum(split.num_rows for split in dataset.values())
    total_columns = len(dataset["train"].features)
    dataset_info = {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "train_size": dataset["train"].num_rows,
        "test_size": dataset["test"].num_rows,
        "val_size": dataset["validation"].num_rows,
    }
    return dataset_info


@beartype
def update_dataset_splits(
    datasetdict: DatasetDict, new_splits: object, is_random: bool
) -> DatasetDict:
    """Splits an already separated dataset by concatenating it and applying
    new splits. The splits could be random by giving numbers between 0 and 1
    in new_splits parameters and setting the is_random parameter to True, or
    the could be manually selected by giving lists of indices to new_splits
    parameter and setting the is_random parameter to False.

    Args:
        datasetdict (DatasetDict): Dataset to update splits
        new_splits (object): Object with the new train, test and validation config
        is_random (bool): If the new splits are random by percentage

    Returns:
        DatasetDict: New DatasetDict with the new splits configuration
    """
    concatenated_dataset = concatenate_datasets(
        [datasetdict["train"], datasetdict["test"], datasetdict["validation"]]
    )
    n = len(concatenated_dataset)
    if is_random:
        check_split_values(
            new_splits["train"], new_splits["test"], new_splits["validation"]
        )
        train_indexes, test_indexes, val_indexes = split_indexes(
            n, new_splits["train"], new_splits["test"], new_splits["validation"]
        )
    else:
        train_indexes = new_splits["train"]
        test_indexes = new_splits["test"]
        val_indexes = new_splits["validation"]
    return split_dataset(
        dataset=concatenated_dataset,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )
