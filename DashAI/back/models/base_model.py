"""Base Model abstract class."""

import json
import os
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Final, Optional

from DashAI.back.config_object import ConfigObject


class BaseModel(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all machine learning models.

    All models must extend this class and implement save and load methods.
    """

    TYPE: Final[str] = "Model"

    @abstractmethod
    def save(self, filename: Optional[str] = None) -> Optional[bytes]:
        """Store an instance of a model.

        Parameters
        ----------

        filename : Optional[str]
            Indicates where to store the model, if filename is None this method returns
            a byte array with the model.

        Returns
        ----------
        Optional[bytes]
            If the filename is None returns the byte array associated with the model.
        """
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
        filename: Optional[str] = None,
        byte_array: Optional[bytes] = None,
    ) -> "BaseModel":
        """Restores an instance of a model.

        Parameters
        ----------
        filename: Optional[str]
            Indicates where the model was stored.
        byte_array: Optional[bytes]
            The bytes associated with the model.

        Returns
        ----------
        BaseModel
            The loaded model.
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
