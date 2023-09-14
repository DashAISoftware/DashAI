from abc import abstractmethod
from typing import Final


class BasePreprocessor:
    """Base class for DashAI preprocessor."""

    TYPE: Final[str] = "Preprocessor"

    @abstractmethod
    def process(self, dataset):
        """Process the dataset.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be processed

        Returns
        -------
        DatasetDict
            Processed dataset
        """
        raise NotImplementedError
