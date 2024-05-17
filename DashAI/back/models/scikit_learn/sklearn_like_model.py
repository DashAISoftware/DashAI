import pickle
from typing import Optional, Type

import joblib

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.base_model import BaseModel


class SklearnLikeModel(BaseModel):
    """Abstract class to define the way to save sklearn like models."""

    def save(self, filename: Optional[str] = None) -> Optional[bytes]:
        """Save the model in the specified path or return the associated bytes."""
        if filename:
            joblib.dump(self, filename)
        else:
            return pickle.dumps(self)

    @staticmethod
    def load(
        filename: Optional[str] = None, byte_array: Optional[bytes] = None
    ) -> "SklearnLikeModel":
        """Load the model of the specified path or from the byte array."""
        if filename:
            model = joblib.load(filename)
        elif byte_array:
            model = pickle.loads(byte_array)
        else:
            raise ValueError(
                "Must pass filename or byte_array yo load method, none of both passed."
            )
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

    def predict(self, x_pred: DashAIDataset):
        """Make a prediction with the model.

        Parameters
        ----------
        x_pred : DashAIDataset
            Dataset with the input data columns.

        Returns
        -------
        array-like
            Array with the predicted target values for x_pred
        """
        return super().predict_proba(x_pred.to_pandas())
