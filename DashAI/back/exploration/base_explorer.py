from abc import ABC, abstractmethod

from beartype.typing import Any, Dict, Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseExplorer(ConfigObject, ABC):
    """Base class for explorers."""

    TYPE: Final[str] = "Explorer"

    @abstractmethod
    def launch_exploration(self, dataset: DashAIDataset) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_results(self, exploration_path: str) -> Dict[str, Any]:
        raise NotImplementedError
