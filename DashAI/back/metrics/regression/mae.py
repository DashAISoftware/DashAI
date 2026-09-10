"""DashAI MAE regression metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MAE(RegressionMetric):
    """Average of absolute differences between predicted and true values.

    Mean Absolute Error (MAE) is the simplest regression error metric: it
    computes the mean of the absolute residuals. Unlike MSE or RMSE, MAE
    treats all errors equally regardless of magnitude, making it more robust
    to outliers. Its value is expressed in the same unit as the target
    variable, which aids interpretability.

    ::

        MAE(y, ŷ) = (1/N) · Σᵢ |yᵢ - ŷᵢ|

    Range: [0, +∞), lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Average of absolute differences between predicted and actual values, "
            "provides a clear measure of prediction accuracy."
        ),
        es=(
            "Promedio de las diferencias absolutas entre valores predichos y reales, "
            "proporciona una medida clara de la precisión de predicción."
        ),
        pt=(
            "Média das diferenças absolutas entre valores previstos e reais, "
            "fornece uma medida clara da acurácia de previsão."
        ),
        de=(
            "Durchschnitt der absoluten Differenzen zwischen vorhergesagten und "
            "tatsächlichen Werten, "
            "bietet ein klares Maß für die Vorhersagegenauigkeit."
        ),
        zh=("预测值与实际值之间绝对差的平均值，提供预测精度的直观度量。"),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        pred_values: "np.ndarray",
    ) -> float:
        """Calculate the MAE between true values and predicted values.

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
            MAE score between true values and predicted values
        """
        from sklearn.metrics import mean_absolute_error

        true_values, pred_values = prepare_to_metric(true_values, pred_values)
        return mean_absolute_error(true_values, pred_values)
