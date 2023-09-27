from beartype import beartype
from datasets import DatasetDict

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.preprocessor.base_transformer import BaseTransformer


class DropColumnByNameTransformer(BaseTransformer):
    """Transformer to drop columns from the dataset"""

    @beartype
    def __init__(self, columns: list[str] | str):
        """Constructor with columns to be dropped by column name

        Parameters
        ----------
        columns : list[str] | str
            Columns to be dropped. The list contains the names of the columns to be
            dropped. The string contains the name of the column to be dropped.
        """
        self.columns = columns

    @beartype
    def fit(self, dataset: DatasetDict) -> BaseTransformer:
        """Fit the transformer.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to fit the transformer
        """
        return self

    @beartype
    def transform(self, dataset: DatasetDict) -> DatasetDict:
        """Transform the dataset by removing columns.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be transformed

        Returns
        -------
        DatasetDict
            Dataset transformed
        """
        for split in dataset:
            dataset[split] = dataset[split].remove_columns(self.columns)
        return dataset

    @beartype
    def transform_dashaidataset(self, dataset: DatasetDict) -> DatasetDict:
        """Transform the dataset by removing columns.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be transformed

        Returns
        -------
        DatasetDict
            Dataset transformed
        """
        for split in dataset:
            dataset_split: DashAIDataset = dataset[split]
            dataset_split = dataset_split.remove_columns(self.columns)
            dataset_split.inputs_columns = [
                col for col in dataset_split.inputs_columns if col not in self.columns
            ]
            dataset[split] = dataset_split
        return dataset
