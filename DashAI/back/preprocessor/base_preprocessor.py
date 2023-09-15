from abc import ABCMeta, abstractmethod
from typing import Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BasePreprocessor(ConfigObject, metaclass=ABCMeta):
    """Base class for DashAI preprocessor."""

    TYPE: Final[str] = "Preprocessor"

    @abstractmethod
    def transform(self, dataset: DashAIDataset) -> DashAIDataset:
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
