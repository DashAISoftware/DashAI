from typing import Type

import joblib
import pandas as pd

from DashAI.back.models.base_model import BaseModel


class SklearnLikeModel(BaseModel):
    """Abstract class to define the way to save sklearn like models."""

    def save(self, filename: str) -> None:
        """Save the model in the specified path."""
        joblib.dump(self, filename)

    @staticmethod
    def load(filename: str) -> None:
        """Load the model of the specified path."""
        model = joblib.load(filename)
        return model

    # --- Methods for process the data for sklearn models ---

    def fit(self, x: pd.DataFrame, y: pd.DataFrame) -> Type["SklearnLikeModel"]:
        """Fit the estimator.

        Parameters
        ----------
        x : pd.DataFrame
            Dataframe with the input data.
        y : pd.DataFrame
            Dataframe with the output data.

        Returns
        -------
        self
            The fitted estimator object.
        """
        return super().fit(x, y)

    def predict(self, x: pd.DataFrame):
        return super().predict_proba(x)
