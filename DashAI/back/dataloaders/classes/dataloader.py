"""DashAI base class for dataloaders."""
import io
import json
import logging
import os
import zipfile
from abc import abstractmethod
from typing import Any, Dict, Final, List, Union

import numpy as np
from beartype import beartype
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from starlette.datastructures import UploadFile

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logger = logging.getLogger(__name__)


class BaseDataLoader(ConfigObject):
    """Abstract class with base methods for DashAI dataloaders."""

    TYPE: Final[str] = "DataLoader"

    @abstractmethod
    def load_data(
        self,
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load data abstract method.

        Parameters
        ----------
        filepath_or_buffer : Union[UploadFile, str], optional
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        raise NotImplementedError

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
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

    def _check_split_values(
        self,
        dataset: DatasetDict,
        train_size: float,
        test_size: float,
        val_size: float,
        stratify: bool = False,
        class_column: Union[str, None] = None,
    ) -> None:
        if stratify and class_column is None:
            raise ValueError("Stratify requires that class_column is not none")

        if (
            class_column is not None
            and class_column not in dataset["train"].column_names
        ):
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

    @beartype
    def split_dataset(
        self,
        dataset: DatasetDict,
        train_size: float,
        test_size: float,
        val_size: float,
        seed: Union[int, None] = None,
        shuffle: bool = True,
        stratify: bool = False,
        class_column: Union[str, None] = None,
    ) -> DatasetDict:
        """Split the dataset in train, test and validation subsets.

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
        dataset : DatasetDict
            A HuggingFace DatasetDict containing the dataset to be split.
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
        stratify : bool, optional
            True indicates the split will be stratified, by default False
        class_column : str, optional
            Indicate the column with which to stratify, by default None

        Returns
        -------
        DatasetDict
            The split dataset.
        """
        self._check_split_values(
            dataset, train_size, test_size, val_size, stratify, class_column
        )

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
            separate_dataset_dict
        )
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
