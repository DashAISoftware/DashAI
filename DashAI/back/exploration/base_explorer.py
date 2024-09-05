from abc import ABC, abstractmethod
from typing import Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseExplorer(ConfigObject, ABC):
    """Base class for explorers."""

    TYPE: Final[str] = "Explorer"

    @abstractmethod
    def launch_exploration(self, dataset: DashAIDataset) -> DashAIDataset:
        raise NotImplementedError
