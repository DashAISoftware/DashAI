from typing import Type
from DashAI.back.converters.base_converter import BaseConverter
from sklearn.base import BaseEstimator

import pandas as pd


class SklearnLikeConverter(BaseConverter, BaseEstimator):
    """Abstract class to define the way to fit and transform sklearn like converters."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fit(self, dataset: pd.DataFrame) -> Type["SklearnLikeConverter"]:
        """Fit the converter.

        Parameters
        ----------
        dataset : Pandas DataFrame
            Dataset to fit the converter

        Returns
        -------
        self
            The fitted converter object.
        """
        return super().fit(dataset)

    def transform(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Transform the dataset.

        Parameters
        ----------
        dataset : Pandas DataFrame
            Dataset to be converted

        Returns
        -------
            Dataset converted
        """
        return super().transform(dataset)
