"""DashAI Dataset implementation."""
import json
import os
from typing import Dict, List, Literal, Tuple, Union

import numpy as np
from beartype import beartype
from datasets import ClassLabel, Dataset, DatasetDict, Value, load_from_disk
from datasets.table import Table


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
def save_dataset(datasetdict: DatasetDict, path: str) -> None:
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
def parse_columns_indices(dataset_path: str, indices: List[int]) -> List[str]:
    """Returns the column labes of the dataset that correspond to the indices

    Args:
        dataset_path (str): Path where the dataset is stored
        indices (List[int]): List with the indices of the columns

    Returns:
        List[str]: List with the labels of the columns
    """
    dataset = load_dataset(dataset_path=dataset_path)
    dataset_features = list((dataset["train"].features).keys())
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
