from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final

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
