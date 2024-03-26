import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Final, List, Tuple

from datasets import DatasetDict

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.base_model import BaseModel


class BaseLocalExplainer(ConfigObject, ABC):
    """Base class for local explainers."""

    TYPE: Final[str] = "LocalExplainer"

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/explainers_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    def fit(self, dataset: Tuple[DatasetDict, DatasetDict], *args, **kwargs):
        return self

    @abstractmethod
    def explain_instance(self, instances: DatasetDict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def plot(self, explanation: dict) -> List[dict]:
        raise NotImplementedError
