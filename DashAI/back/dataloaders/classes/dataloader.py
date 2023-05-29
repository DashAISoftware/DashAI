import io
import json
import logging
import zipfile
from abc import abstractmethod
from typing import Final, List

from datasets import Dataset, DatasetDict
from fastapi import UploadFile

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logger = logging.getLogger(__name__)


class BaseDataLoader(ConfigObject):
    """
    Abstract class with base methods for all data loaders
    """

    TYPE: Final[str] = "DataLoader"

    @abstractmethod
    def load_data(self, dataset_path, file=None, url=None):
        raise NotImplementedError

    @classmethod
    def get_schema(self):
        """
        This method load the schema JSON file asocciated to the dataloader.
        """
        try:
            with open(
                f"DashAI/back/dataloaders/description_schemas/{self.__name__}.json", "r"
            ) as f:
                schema = json.load(f)
            return schema
        except FileNotFoundError:
            logger.exception(
                (
                    f"Could not load the schema for {self.__name__} : File DashAI/back"
                    f"/dataloaders/description_schemas/{self.__name__}.json not found."
                )
            )
            return {}

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

        First the dataset is splitted into a train and test-validation splits.
        This is because the validation split is taken from a portion of the test split.
        For that the size of the test split for the first split is
        the sum of the sizes of test and validation splits.
        Then, the test and validation splits are defined in the second split,
        where now the train size of this split is the final test split and the result
        of the test split is actually the validation split. So that ‘val_size’
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
        if stratify:
            stratify_column = class_column
        else:
            stratify_column = None

        test_val = test_size + val_size
        val_proportion = test_size / test_val
        inputs_columns = dataset["train"].inputs_columns
        outputs_columns = dataset["train"].outputs_columns
        train_split = dataset["train"].train_test_split(
            train_size=train_size,
            shuffle=shuffle,
            seed=seed,
            stratify_by_column=stratify_column,
        )
        test_valid_split = train_split["test"].train_test_split(
            train_size=val_proportion,
            shuffle=shuffle,
            seed=seed,
            stratify_by_column=stratify_column,
        )
        dataset["train"] = train_split["train"]
        dataset["test"] = test_valid_split["train"]
        dataset["validation"] = test_valid_split["test"]

        train_dataset_dict = dataset["train"].to_dict()
        test_dataset_dict = dataset["test"].to_dict()
        validation_dataset_dict = dataset["validation"].to_dict()

        train_dataset = Dataset.from_dict(train_dataset_dict)
        test_dataset = Dataset.from_dict(test_dataset_dict)
        validation_dataset = Dataset.from_dict(validation_dataset_dict)

        separate_dataset_dict = DatasetDict(
            {
                "train": train_dataset,
                "test": test_dataset,
                "validation": validation_dataset,
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
    Convert all datasets within the DatasetDict to type DashAIDataset

    Returns:
        DatasetDict: Datasetdict with datasets converted to DashAIDataset
    """
    for i in dataset.keys():
        dataset[i] = DashAIDataset(dataset[i].data, inputs_columns, outputs_columns)
    return dataset
