from base_preprocessor import BasePreprocessor
from datasets import DatasetDict


class RemoveColumnsPreprocessor(BasePreprocessor):
    """Preprocessor that removes columns from the dataset."""

    def process(self, dataset: DatasetDict, initial_index: int, final_index: int):
        """Process the dataset.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be processed

        initial_index : int
            Initial index of the columns to be removed

        final_index : int
            Final index of the columns to be removed

        Returns
        -------
        DatasetDict
            Processed dataset
        """
        for split in dataset:
            dataset[split] = dataset[split].remove_columns(
                dataset[split].column_names[initial_index:final_index]
            )
        return dataset
