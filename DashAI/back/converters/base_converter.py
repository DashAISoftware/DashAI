from __future__ import annotations

import json
import os
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Final

from datasets import DatasetDict
from sklearn.base import BaseEstimator, TransformerMixin

from DashAI.back.config_object import ConfigObject


class BaseConverter(ConfigObject, BaseEstimator, TransformerMixin, metaclass=ABCMeta):
    """Base class for all converters"""

    TYPE: Final[str] = "Converter"

    @abstractmethod
    def fit(self, dataset: DatasetDict) -> "BaseConverter":
        """Fit the converter.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to fit the converter
        """
        raise NotImplementedError

    @abstractmethod
    def transform(self, dataset: DatasetDict) -> DatasetDict:
        """Transform the dataset.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be converted

        Returns
        -------
            Dataset converted
        """
        raise NotImplementedError

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/params_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)
