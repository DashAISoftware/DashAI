from base_transformer import BaseTransformer
from datasets import DatasetDict


class DropColumnTransformer(BaseTransformer):
    """Transformer to drop columns from the dataset"""

    def transform(self, dataset: DatasetDict, initial_index: int, final_index: int):
        """Transform the dataset by removing columns.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be transformed

        initial_index : int
            Initial index of the columns to be removed

        final_index : int
            Final index of the columns to be removed

        Returns
        -------
        DatasetDict
            Dataset transformed
        """
        for split in dataset:
            dataset[split] = dataset[split].remove_columns(
                dataset[split].column_names[initial_index:final_index]
            )
        return dataset
