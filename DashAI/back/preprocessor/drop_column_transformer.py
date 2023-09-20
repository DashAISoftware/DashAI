from base_transformer import BaseTransformer
from datasets import DatasetDict


class DropColumnTransformer(BaseTransformer):
    """Transformer to drop columns from the dataset"""

    def __init__(self, columns: list[str] | str | tuple[int, int]):
        """Constructor

        Parameters
        ----------
        columns : list[str] | str | tuple[int, int]
            Columns to be dropped. In case of the list or str, the columns are dropped
            by name. In case of the tuple, the dropped columns will be those between
            the two indexes.
        """
        self.columns = columns

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
            if isinstance(self.columns, (list, str)):
                dataset[split] = dataset[split].remove_columns(self.columns)
            elif isinstance(self.columns, tuple):
                dataset[split] = dataset[split].remove_columns(
                    dataset[split].column_names[self.columns[0] : self.columns[1]]
                )
        return dataset
