from typing import List, Type

from beartype import beartype
from datasets import DatasetDict

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ColumnDropper(BaseConverter):
    """Converter to drop columns by index."""

    @beartype
    def __init__(self):
        """Constructor with columns to be dropped by column index."""
        self.columns_names: List[str] = []

    @beartype
    def fit(self, dataset: DatasetDict) -> Type["BaseConverter"]:
        """Fit the converter.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to fit the converter
        """
        return self

    @beartype
    def transform(
        self, dataset: DatasetDict, columns_indexes: List[int]
    ) -> DatasetDict:
        """Convert the dataset by removing columns.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be converted
        columns_indexes : List[int]
            Columns indexes to be dropped

        Returns
        -------
        DatasetDict
            Dataset converted
        """
        # first, we check if the columns indexes are valid
        for index in columns_indexes:
            if index < 0 or index >= len(dataset["train"].column_names):
                raise ValueError(
                    f"Column index {index} is not valid for dataset with columns "
                    f"{dataset['train'].column_names}"
                )
        for split in dataset:
            dataset_split: DashAIDataset = dataset[split]
            if self.columns_names == []:
                self.columns_names = [
                    dataset_split.column_names[index] for index in columns_indexes
                ]
            dataset_split = dataset_split.remove_columns(self.columns_names)
            dataset[split] = dataset_split
        return dataset
