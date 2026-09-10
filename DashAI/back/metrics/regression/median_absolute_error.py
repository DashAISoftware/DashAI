"""Median Absolute Error metric for regression tasks."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MedianAbsoluteError(RegressionMetric):
    """Median of absolute differences between predicted and true values.

    Median Absolute Error (MedAE) is a robust regression metric that uses the
    median rather than the mean of the absolute residuals. Because the median
    is insensitive to extreme values, MedAE is far less affected by outliers
    than MAE, MSE, or RMSE, making it the preferred metric when the target
    distribution has heavy tails or occasional extreme measurements.

    ::

        MedAE(y, ŷ) = median( |y₁ - ŷ₁|, …, |yₙ - ŷₙ| )

    Range: [0, +∞), lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.median_absolute_error.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Median Absolute Error (MedAE) measures the median "
            "of the absolute differences "
            "between predicted values and actual values in a regression model. "
            "It provides a robust measure of prediction accuracy, "
            "less sensitive to outliers "
            "compared to Mean Absolute Error (MAE)."
        ),
        es=(
            "El Error Absoluto Mediano (MedAE) mide la mediana "
            "de las diferencias absolutas "
            "entre valores predichos y reales en un modelo de regresión. "
            "Proporciona una medida robusta de la precisión de predicción, "
            "menos sensible a valores atípicos "
            "en comparación con el Error Absoluto Medio (MAE)."
        ),
        pt=(
            "O Erro Absoluto Mediano (MedAE) mede a mediana "
            "das diferenças absolutas "
            "entre valores previstos e reais em um modelo de regressão. "
            "Fornece uma medida robusta de precisão de previsão, "
            "menos sensível a valores atípicos "
            "em comparação com o Erro Absoluto Médio (MAE)."
        ),
        de=(
            "Mittlerer Absoluter Fehler (MedAE) misst den Median "
            "der absoluten Differenzen "
            "zwischen vorhergesagten und tatsächlichen Werten in einem "
            "Regressionsmodell. "
            "Er bietet ein robustes Maß für die Vorhersagegenauigkeit, "
            "das weniger empfindlich gegenüber Ausreißern ist "
            "als der Mittlere Absolute Fehler (MAE)."
        ),
        zh=(
            "中位绝对误差（MedAE）衡量回归模型中预测值与实际值绝对差的中位数，"
            "比平均绝对误差对异常值更为鲁棒。"
        ),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        predicted_values: "np.ndarray",
    ) -> float:
        """Calculate the Median Absolute Error between true values and predicted values.

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
            Median Absolute Error score between true values and predicted values
        """
        from sklearn.metrics import median_absolute_error

        true_values, pred_values = prepare_to_metric(true_values, predicted_values)
        return median_absolute_error(true_values, pred_values)
