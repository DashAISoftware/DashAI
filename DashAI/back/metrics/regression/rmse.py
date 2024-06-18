"""DashAI RMSE regression metric implementation."""

import numpy as np
from sklearn.metrics import mean_squared_error

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric


class RMSE(RegressionMetric):
    """Root Mean Squared Error metric for regression tasks."""

    @staticmethod
    def score(true_values: DashAIDataset, predicted_values: np.ndarray) -> float:
        """Calculate the RMSE between true values and predicted values.

        Parameters
        ----------
        true_values : DashAIDataset
            A DashAI dataset with true values.
        predicted_values : np.ndarray
            A one-dimensional array with the predicted values
            for each instance.

        Returns
        -------
        float
            RMSE score between true values and predicted values
        """
        true_values, pred_values = prepare_to_metric(true_values, predicted_values)
        return mean_squared_error(true_values, pred_values, squared=False)
