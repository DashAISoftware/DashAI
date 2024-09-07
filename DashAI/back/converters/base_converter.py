from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final, Type

import pandas as pd

from DashAI.back.config_object import ConfigObject


class BaseConverter(ConfigObject, metaclass=ABCMeta):
    """
    Base class for all converters

    Converters are for modifying the data in a supervised or unsupervised way
    (e.g. by adding, changing, or removing columns, but not by adding or removing rows)
    """

    TYPE: Final[str] = "Converter"

    @abstractmethod
    def fit(self, dataset: pd.DataFrame) -> Type[BaseConverter]:
        """Fit the converter.

        Parameters
        ----------
        dataset : Pandas DataFrame
            Dataset to fit the converter

        Returns
        ----------
        self
            The fitted converter object.
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
