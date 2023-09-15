from abc import abstractmethod
from typing import Final


from abc import ABCMeta, abstractmethod
from DashAI.back.config_object import ConfigObject


class BasePreprocessor(ConfigObject, metaclass=ABCMeta):
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
