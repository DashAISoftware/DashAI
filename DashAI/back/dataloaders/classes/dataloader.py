import io
import zipfile
from abc import abstractmethod

from datasets import DatasetDict
from fastapi import UploadFile

from DashAI.back.config_object import ConfigObject


class BaseDataLoader(ConfigObject):
    """
    Abstract class with base methods for all data loaders
    """

    @abstractmethod
    def load_data(self, dataset_path, file=None, url=None):
        raise NotImplementedError

    def extract_files(self, dataset_path: str, file: UploadFile) -> str:
        """
        Extract the files to load the data in a DataDict later.

        Args:
            dataset_path (str): Path where dataset will be saved.
            file (UploadFile): File uploaded for the user.

        Returns:
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

        Args:
            dataset (DatasetDict): Dataset in Hugging Face format.
            train_size (float): Proportion of the dataset for train split (in 0-1).
            test_size (float): Proportion of the dataset for test split (in 0-1).
            val_size (float): Proportion of the dataset for validation split (in 0-1).
            seed (int): For control the reproducibility.
            shuffle (bool): True if data will be shuffle when splitting the dataset.
            stratify (bool): Indicates if the split will be stratified.
            class_column (str): Indicate the column with which to stratify.

        Returns:
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
        if not isinstance(seed, int):
            raise TypeError(f"seed should be an integer, got {type(seed)}")
        if not isinstance(shuffle, bool):
            raise TypeError(f"shuffle should be a boolean, got {type(shuffle)}")
        if not isinstance(stratify, bool):
            raise TypeError(f"stratify should be a boolean, got {type(stratify)}")
        if not isinstance(class_column, str):
            raise TypeError(
                f"class_column should be a string, got {type(class_column)}"
            )

        # Value checks
        if class_column not in dataset["train"].column_names:
            raise ValueError(f"Column '{class_column}' do not exist in the dataset.")
        if train_size < 0 or train_size > 1:
            raise ValueError(
                "train_size should be in the (0, 1) range "
                + f"(0 and 1 not included), got {val_size}"
            )
        if test_size < 0 or test_size > 1:
            raise ValueError(
                "test_size should be in the (0, 1) range "
                + f"(0 and 1 not included), got {val_size}"
            )
        if val_size < 0 or val_size > 1:
            raise ValueError(
                "val_size should be in the (0, 1) range "
                + f"(0 and 1 not included), got {val_size}"
            )

        # The splitting are made twice -------------------------------------------
        # First the dataset is splitting into a train split and a test-val split,
        # this is because the validation split is taken like a portion of
        # the test split of the first splitting (test-val).

        # Then, the test and validation splits are defined in the second splitting
        # where now, the train size of this splitting is the final test split and
        # the result of the test split is actually the validation split.
        # -------------------------------------------------------------------------
        if stratify:
            stratify_column = class_column
        else:
            stratify_column = None

        test_val = test_size + val_size
        val_proportion = val_size / test_val
        train_split = dataset["train"].train_test_split(
            test_size=test_val,
            train_size=train_size,
            shuffle=shuffle,
            seed=seed,
            stratify_by_column=stratify_column,
        )
        test_valid_split = train_split["test"].train_test_split(
            test_size=val_proportion,
            shuffle=shuffle,
            seed=seed,
            stratify_by_column=stratify_column,
        )
        dataset["train"] = train_split["train"]
        dataset["test"] = test_valid_split["train"]
        dataset["validation"] = test_valid_split["test"]
        return dataset
