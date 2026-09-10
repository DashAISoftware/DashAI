"""DashAI MSE regression metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MSE(RegressionMetric):
    """Average of squared differences between predicted and true values.

    Mean Squared Error (MSE) squares each residual before averaging, which
    penalises large errors much more heavily than small ones. This makes MSE
    sensitive to outliers: a single large prediction error can dominate the
    score. It is the most widely used regression loss and is the basis for
    ordinary least-squares regression and RMSE.

    ::

        MSE(y, ŷ) = (1/N) · Σᵢ (yᵢ - ŷᵢ)²

    Range: [0, +∞), lower is better (``MAXIMIZE = False``). Units are the
    square of the target variable's unit (use RMSE for the original unit).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_squared_error.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Mean Squared Error (MSE) measures the average "
            "of the squared differences "
            "between predicted values and actual values in a regression model. "
            "It provides an indication of the model's prediction accuracy, "
            "with lower values indicating better fit."
        ),
        es=(
            "El Error Cuadrático Medio (MSE) mide el promedio "
            "de las diferencias al cuadrado "
            "entre valores predichos y reales en un modelo de regresión. "
            "Indica la precisión de predicción del modelo, "
            "donde valores más bajos indican mejor ajuste."
        ),
        pt=(
            "O Erro Quadrático Médio (MSE) mede a média "
            "das diferenças ao quadrado "
            "entre valores previstos e reais em um modelo de regressão. "
            "Indica a acurácia de previsão do modelo, "
            "com valores mais baixos indicando melhor ajuste."
        ),
        de=(
            "Mittlerer Quadratischer Fehler (MSE) misst den Durchschnitt "
            "der quadrierten Differenzen "
            "zwischen vorhergesagten und tatsächlichen Werten in einem "
            "Regressionsmodell. "
            "Er gibt einen Hinweis auf die Vorhersagegenauigkeit des Modells, "
            "wobei niedrigere Werte eine bessere Anpassung anzeigen."
        ),
        zh=(
            "均方误差（MSE）衡量回归模型中预测值与实际值平方差的平均值，"
            "值越低表示拟合越好。"
        ),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        predicted_values: "np.ndarray",
    ) -> float:
        """Calculate the MSE between true values and predicted values.

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
            MSE score between true values and predicted values
        """
        from sklearn.metrics import mean_squared_error

        true_values, pred_values = prepare_to_metric(true_values, predicted_values)
        return mean_squared_error(true_values, pred_values)
