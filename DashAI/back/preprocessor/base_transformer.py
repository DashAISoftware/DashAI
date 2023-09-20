from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final

from sklearn.base import BaseEstimator, TransformerMixin

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseTransformer(ConfigObject, BaseEstimator, TransformerMixin, metaclass=ABCMeta):
    """Base class for all transformers"""

    TYPE: Final[str] = "Transformer"

    @abstractmethod
    def fit(self, dataset: DashAIDataset) -> BaseTransformer:
        """Fit the transformer.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to fit the transformer
        """
        raise NotImplementedError

    @abstractmethod
    def transform(self, dataset: DashAIDataset) -> DashAIDataset:
        """Transform the dataset.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to be transformed

        Returns
        -------
            Dataset transformed
        """
        raise NotImplementedError
