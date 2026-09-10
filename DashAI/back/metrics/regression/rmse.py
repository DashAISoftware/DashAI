"""DashAI RMSE regression metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class RMSE(RegressionMetric):
    """Square root of the mean squared error between predicted and true values.

    Root Mean Squared Error (RMSE) is the square root of MSE, bringing the
    metric back to the same unit as the target variable. Like MSE, it
    penalises large errors more heavily than MAE, but its interpretability
    advantage over MSE makes it the standard regression error metric in most
    applications. RMSE is equivalent to the Euclidean distance between the
    prediction vector and the true value vector, normalised by sample count.

    ::

        RMSE(y, ŷ) = sqrt( (1/N) · Σᵢ (yᵢ - ŷᵢ)² )

    Range: [0, +∞), lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.root_mean_squared_error.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Square root of the average of squared differences between "
            "predicted and actual values, penalizes larger errors more heavily."
        ),
        es=(
            "Raíz cuadrada del promedio de las diferencias al cuadrado entre "
            "valores predichos y reales, penaliza más los errores grandes."
        ),
        pt=(
            "Raiz quadrada da média das diferenças ao quadrado entre "
            "valores previstos e reais, penaliza mais os erros grandes."
        ),
        de=(
            "Quadratwurzel des Durchschnitts der quadrierten Differenzen zwischen "
            "vorhergesagten und tatsächlichen Werten, bestraft größere Fehler stärker."
        ),
        zh=("预测值与实际值平方差均值的平方根，对较大误差的惩罚更重。"),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        predicted_values: "np.ndarray",
    ) -> float:
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
        from sklearn.metrics import root_mean_squared_error

        true_values, pred_values = prepare_to_metric(true_values, predicted_values)
        return root_mean_squared_error(true_values, pred_values)
