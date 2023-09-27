from beartype import beartype
from datasets import DatasetDict

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.preprocessor.base_transformer import BaseTransformer


class DropColumnByIndexTransformer(BaseTransformer):
    """Transformer to drop columns from the dataset by column index"""

    @beartype
    def __init__(self, columns: tuple[int, int]):
        """Constructor with columns to be dropped by column index

        Parameters
        ----------
        columns : tuple[int, int]
            Columns to be dropped. The tuple contains the start and end index of the
            columns to be dropped.
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
            dataset_split: DashAIDataset = dataset[split]
            column_names_to_drop = dataset[split].column_names[
                self.columns[0] : self.columns[1]
            ]
            dataset_split = dataset_split.remove_columns(column_names_to_drop)
            dataset_split.inputs_columns = [
                col for col in dataset_split.inputs_columns if col not in self.columns
            ]
            dataset[split] = dataset_split
        return dataset
