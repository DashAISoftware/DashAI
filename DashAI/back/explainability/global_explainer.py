import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Final, Tuple

from datasets import DatasetDict

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.base_model import BaseModel


class BaseGlobalExplainer(ConfigObject, ABC):
    """Base class for global explainers."""

    TYPE: Final[str] = "GlobalExplainer"

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    def save_explanation(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.explanation, f)

    @staticmethod
    def load_explanation(path: str) -> None:
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/explainers_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    @abstractmethod
    def explain(self, dataset: Tuple[DatasetDict, DatasetDict]):
        raise NotImplementedError
