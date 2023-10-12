from typing import Type

from beartype import beartype
from datasets import DatasetDict

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ColumnDropperByIndex(BaseConverter):
    """Converter to drop columns from the dataset by column index"""

    @beartype
    def __init__(self, columns_index: tuple[int, int] | int):
        """Constructor with columns to be dropped by column index

        Parameters
        ----------
        columns : tuple[int, int] | int
            Columns to be dropped. The tuple contains the start and end index of the
            columns to be dropped (both included). The int contains the index of the
            column to be dropped.
        """
        if isinstance(columns_index, int):
            columns_index = [columns_index, columns_index]
        self.columns_index = columns_index

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
    def transform(self, dataset: DatasetDict) -> DatasetDict:
        """Convert the dataset by removing columns.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be converted

        Returns
        -------
        DatasetDict
            Dataset converted
        """
        for split in dataset:
            dataset_split: DashAIDataset = dataset[split]
            column_names_to_drop = dataset[split].column_names[
                self.columns_index[0] : self.columns_index[1] + 1
            ]
            dataset_split = dataset_split.remove_columns(column_names_to_drop)
            dataset[split] = dataset_split
        return dataset
