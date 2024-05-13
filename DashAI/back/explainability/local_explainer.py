from abc import ABC, abstractmethod
from typing import Final, List, Tuple

from datasets import DatasetDict

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.base_model import BaseModel


class BaseLocalExplainer(ConfigObject, ABC):
    """Base class for local explainers."""

    TYPE: Final[str] = "LocalExplainer"

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    def fit(self, dataset: Tuple[DatasetDict, DatasetDict], *args, **kwargs):
        return self

    @abstractmethod
    def explain_instance(self, instances: DatasetDict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def plot(self, explanation: dict) -> List[dict]:
        raise NotImplementedError
