from beartype import beartype
from datasets import DatasetDict

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.preprocessor.base_converter import BaseConverter


class ColumnDropperByName(BaseConverter):
    """Converter to drop columns from the dataset"""

    @beartype
    def __init__(self, column_names: list[str] | str):
        """Constructor with columns to be dropped by column name

        Parameters
        ----------
        columns : list[str] | str
            Columns to be dropped. The list contains the names of the columns to be
            dropped. The string contains the name of the column to be dropped.
        """
        if isinstance(columns, str):
            columns = [columns]
        self.columns = columns

    @beartype
    def fit(self, dataset: DatasetDict) -> BaseConverter:
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
            dataset_split = dataset_split.remove_columns(self.columns)
            dataset[split] = dataset_split
        return dataset
