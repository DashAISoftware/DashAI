from base_transformer import BaseTransformer
from beartype import beartype
from datasets import DatasetDict


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
            dataset[split] = dataset[split].remove_columns(
                dataset.column_names[self.columns[0] : self.columns[1]]
            )
        return dataset
