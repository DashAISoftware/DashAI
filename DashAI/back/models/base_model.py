"""Base Model abstract class."""
import json
import os
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Final

from DashAI.back.config_object import ConfigObject


class BaseModel(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all machine learning models.

    All models must extend this class and implement save and load methods.
    """

    TYPE: Final[str] = "Model"

    # TODO implement a check_params method to check the params
    #  using the JSON schema file.
    # TODO implement a method to check the initialization of TASK
    #  an task params variables.

    @abstractmethod
    def save(self, filename: str) -> None:
        """Store an instance of a model.

        filename (Str): Indicates where to store the model,
        if filename is None, this method returns a bytes array with the model.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, filename: str) -> Any:
        """Restores an instance of a model.

        filename (Str): Indicates where the model was stored.
        """
        raise NotImplementedError

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/parameters/models_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)
