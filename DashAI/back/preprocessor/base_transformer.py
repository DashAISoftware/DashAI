from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final

from datasets import DatasetDict
from sklearn.base import BaseEstimator, TransformerMixin

from DashAI.back.config_object import ConfigObject


class BaseTransformer(ConfigObject, BaseEstimator, TransformerMixin, metaclass=ABCMeta):
    """Base class for all transformers"""

    TYPE: Final[str] = "Transformer"

    @abstractmethod
    def fit(self, dataset: DatasetDict) -> BaseTransformer:
        """Fit the transformer.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to fit the transformer
        """
        raise NotImplementedError

    @abstractmethod
    def transform(self, dataset: DatasetDict) -> DatasetDict:
        """Transform the dataset.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be transformed

        Returns
        -------
            Dataset transformed
        """
        raise NotImplementedError
