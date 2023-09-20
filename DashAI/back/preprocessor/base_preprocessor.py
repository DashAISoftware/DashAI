from abc import ABCMeta, abstractmethod
from typing import Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseTransformer(ConfigObject, metaclass=ABCMeta):
    """Base class for all transformers"""

    TYPE: Final[str] = "Transformer"

    @abstractmethod
    def transform(self, dataset: DashAIDataset) -> DashAIDataset:
        """Transform the dataset.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to be transformed

        Returns
        -------
            Dataset transformed
        """
        raise NotImplementedError
