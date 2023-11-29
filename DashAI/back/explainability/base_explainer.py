import json
import logging
import os
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, Final

from DashAI.back.config_object import ConfigObject


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class BaseExplainer(ConfigObject, ABC):
    """_summary_

    Args:
        ABC (_type_): _description_
    """

    TYPE: Final[str] = "Explainer"

    def __init__(self) -> None:
        pass

    def save(self, filename: str) -> None:
        with open(filename, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, filename: str) -> None:
        with open(filename, "rb") as f:
            return pickle.load(f)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/explainers_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)
