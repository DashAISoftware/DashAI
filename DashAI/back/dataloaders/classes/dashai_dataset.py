"""DashAI Dataset implementation."""
import json
import os
from typing import Dict, List, Literal, Union

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
def get_column_types(dataset_path: str) -> Dict[str, Dict]:
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
            column_types[column] = {"type": "Classlabel", "dtype": ""}
    return column_types


@beartype
def load_dataset(dataset_path: str) -> DatasetDict:
    """Load a datasetdict with dashaidatasets inside.

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


def update_column_types(datasetdict: DatasetDict, columns: Dict) -> None:
    for split in datasetdict:
        datasetdict[split].cast(columns)  ## Esto retorna el dataset
