import io
import json
import logging
import os
import zipfile
from abc import abstractmethod
from typing import Final, List

import numpy as np
from datasets import Dataset, DatasetDict
from fastapi import UploadFile
from sklearn.model_selection import train_test_split

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logger = logging.getLogger(__name__)


class BaseDataLoader(ConfigObject):
    """Abstract class with base methods for all data loaders."""

    TYPE: Final[str] = "DataLoader"

    @abstractmethod
    def load_data(self, dataset_path, file=None, url=None):
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        """Load the JSON schema asocciated to the dataloader."""
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            parent_dir = os.path.dirname(dir_path)
            with open(
                f"{parent_dir}/description_schemas/{cls.__name__}.json",
            ) as f:
                schema = json.load(f)
            return schema

        except FileNotFoundError:
            logger.exception(
                f"Could not load the schema for {cls.__name__} : File DashAI/back"
                f"/dataloaders/description_schemas/{cls.__name__}.json not found.",
            )
            return {}

    def extract_files(self, dataset_path: str, file: UploadFile) -> str:
        """Extract the files to load the data in a DataDict later.

        Args:
            dataset_path (str): Path where dataset will be saved.
            file (UploadFile): File uploaded for the user.

        Returns
        -------
            str: Path of the files extracted.
        """
        if file.content_type == "application/zip":
            files_path = f"{dataset_path}/files"
            with zipfile.ZipFile(io.BytesIO(file.file.read()), "r") as zip_file:
                zip_file.extractall(path=files_path)
        else:
            files_path = f"{dataset_path}/{file.filename}"
            with open(files_path, "wb") as f:
                f.write(file.file.read())
        return files_path

    def split_dataset(
        self,
        dataset: DatasetDict,
        train_size: float,
        test_size: float,
        val_size: float,
        seed: int = None,
        shuffle: bool = True,
        stratify: bool = False,
        class_column: str = None,
    ) -> DatasetDict:
        """
        Split the dataset in train, test and validation data.

        First the dataset is splitted into a train and test-validation splits.
        This is because the validation split is taken from a portion of the test split.
        For that the size of the test split for the first split is
        the sum of the sizes of test and validation splits.
        Then, the test and validation splits are defined in the second split,
        where now the train size of this split is the final test split and the result
        of the test split is actually the validation split. So that `val_size`
        is the proportion of the validation split of the rest of the data in the
        resulting test split.
        An example, if we have a train size of 0.8, a test size of 0.1 and a validation
        size of 0.1. In the first process we split the data in the train data
        with the 80% of the data, and a test-validation data with the 20% remaining.
        Then in then second process we divide this 20% in a 50% test and 50% validation.
        Args:
            dataset (DatasetDict): Dataset in Hugging Face format.
            train_size (float): Proportion of the dataset for train split (in 0-1).
            test_size (float): Proportion of the dataset for test split (in 0-1).
            val_size (float): Proportion of the dataset for validation split (in 0-1).
            seed (int): For control the reproducibility.
            shuffle (bool): True if data will be shuffle when splitting the dataset.
            stratify (bool): Indicates if the split will be stratified.
            class_column (str): Indicate the column with which to stratify.

        Returns
        -------
            DatasetDict: The dataset splitted in train, test and validation splits.
        """
        # Type checks
        if not isinstance(dataset, DatasetDict):
            raise TypeError(f"dataset should be a DatasetDict, got {type(dataset)}")
        if not isinstance(train_size, float):
            raise TypeError(f"train_size should be a float, got {type(train_size)}")
        if not isinstance(test_size, float):
            raise TypeError(f"test_size should be a float, got {type(test_size)}")
        if not isinstance(val_size, float):
            raise TypeError(f"val_size should be a float, got {type(val_size)}")
        if not isinstance(seed, (int, type(None))):
            raise TypeError(f"seed should be an integer, got {type(seed)}")
        if not isinstance(shuffle, bool):
            raise TypeError(f"shuffle should be a boolean, got {type(shuffle)}")
        if not isinstance(stratify, bool):
            raise TypeError(f"stratify should be a boolean, got {type(stratify)}")
        if not isinstance(class_column, (str, type(None))):
            raise TypeError(
                f"class_column should be a string, got {type(class_column)}"
            )

        # Value checks
        if stratify and class_column is None:
            raise ValueError("Stratify requires that class_column is not none")

        if class_column not in dataset["train"].column_names:
            raise ValueError(f"Column '{class_column}' do not exist in the dataset.")
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

        inputs_columns = dataset["train"].inputs_columns
        outputs_columns = dataset["train"].outputs_columns

        # Get the number of records
        n = len(dataset["train"])

        # Generate shuffled indices
        np.random.seed(seed)
        indices = np.arange(n)

        test_val = test_size + val_size
        val_proportion = test_size / test_val

        # Define stratification array if stratify is True
        stratify_array = (
            np.array(dataset["train"][class_column])
            if stratify and class_column
            else None
        )

        # Split the indices
        train_indices, test_val_indices = train_test_split(
            indices,
            train_size=train_size,
            random_state=seed,
            stratify=stratify_array,
            shuffle=shuffle,
        )
        test_indices, val_indices = train_test_split(
            test_val_indices,
            train_size=val_proportion,
            random_state=seed,
            stratify=stratify_array[test_val_indices]
            if stratify_array is not None
            else None,
            shuffle=shuffle,
        )

        # Convert the indices into boolean masks
        train_mask = np.isin(np.arange(n), train_indices)
        test_mask = np.isin(np.arange(n), test_indices)
        val_mask = np.isin(np.arange(n), val_indices)

        # Get the underlying table
        table = dataset["train"].data

        # Create separate tables for each split
        train_table = table.filter(train_mask)
        test_table = table.filter(test_mask)
        val_table = table.filter(val_mask)

        separate_dataset_dict = DatasetDict(
            {
                "train": Dataset(train_table),
                "test": Dataset(test_table),
                "validation": Dataset(val_table),
            }
        )

        dataset = to_dashai_dataset(
            separate_dataset_dict, inputs_columns, outputs_columns
        )
        return dataset


def to_dashai_dataset(
    dataset: DatasetDict, inputs_columns: List[str], outputs_columns: List[str]
) -> DatasetDict:
    """
    Convert all datasets within the DatasetDict to type DashAIDataset.

    Returns
    -------
        DatasetDict: Datasetdict with datasets converted to DashAIDataset
    """
    for key in dataset:
        dataset[key] = DashAIDataset(dataset[key].data, inputs_columns, outputs_columns)
    return dataset
