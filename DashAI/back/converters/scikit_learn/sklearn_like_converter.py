

from typing import Type
from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from sklearn.base import BaseEstimator


class SklearnLikeConverter(BaseConverter, BaseEstimator):
    """Abstract class to define the way to fit and transform sklearn like converters."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fit(self, dataset: DashAIDataset) -> Type["SklearnLikeConverter"]:
        """Fit the converter.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to be converted

        Returns
        -------
        self
            The fitted converter object.
        """
        x_pandas = dataset.to_pandas()
        return super().fit(x_pandas)

    def transform(self, dataset: DashAIDataset) -> DashAIDataset:
        """Transform the dataset.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to be converted

        Returns
        -------
        DashAIDataset
        """
        x_pandas = dataset.to_pandas()
        return super().transform(x_pandas)