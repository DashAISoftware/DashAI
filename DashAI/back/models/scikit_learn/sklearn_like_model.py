from typing import Type, Union

import joblib
import pandas as pd

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
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

    def fit(
        self, x_train: DashAIDataset, y_train: DashAIDataset
    ) -> Type["SklearnLikeModel"]:
        """Fit the estimator.

        Parameters
        ----------
        x_train : pd.DataFrame
            Dataframe with the input data.
        y_train : pd.DataFrame
            Dataframe with the output data.

        Returns
        -------
        self
            The fitted estimator object.
        """
        x_pandas = x_train.to_pandas()
        y_pandas = y_train.to_pandas()
        return super().fit(x_pandas, y_pandas)

    def predict(self, x_pred: Union[DashAIDataset, pd.DataFrame]):
        """Make a prediction with the model.

        Parameters
        ----------
        x_pred : Union[DashAIDataset, pd.DataFrame]
            Dataset with the input data columns.

        Returns
        -------
        array-like
            Array with the predicted target values for x_pred
        """
        if isinstance(x_pred, DashAIDataset):
            x_pred = x_pred.to_pandas()
        return super().predict_proba(x_pred)
