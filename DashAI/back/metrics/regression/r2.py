"""DashAI R2 score implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class R2(RegressionMetric):
    """Coefficient of determination measuring goodness of fit for regression models.

    R² (R-squared) measures the proportion of variance in the target variable
    that is explained by the model. It compares the model's predictions to a
    trivial baseline that always predicts the target mean. An R² of 1.0 means
    the model explains all variance perfectly; 0.0 means it is no better than
    the mean predictor; negative values indicate worse-than-baseline performance.

    R² is scale-invariant (unlike MAE/MSE), making it easy to compare models
    trained on targets with different units or magnitudes.

    ::

        R²(y, ŷ) = 1 - Σᵢ(yᵢ - ŷᵢ)² / Σᵢ(yᵢ - ȳ)²

    Range: (-∞, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html
    """

    MAXIMIZE: bool = True
    DESCRIPTION = MultilingualString(
        en=(
            "R2 score, also known as the coefficient of determination, "
            "measures how well the predicted values from a regression model "
            "approximate the actual data points. It provides an indication of "
            "the goodness of fit of the model."
        ),
        es=(
            "El puntaje R2, también conocido como coeficiente de determinación, "
            "mide qué tan bien los valores predichos de un modelo de regresión "
            "se aproximan a los datos reales. Proporciona una indicación de "
            "la bondad de ajuste del modelo."
        ),
        pt=(
            "A pontuação R2, também conhecida como coeficiente de determinação, "
            "mede quão bem os valores previstos de um modelo de regressão "
            "se aproximam dos dados reais. Fornece uma indicação da "
            "qualidade do ajuste do modelo."
        ),
        de=(
            "R2-Wertung, auch bekannt als Bestimmtheitsmaß, "
            "misst, wie gut die vorhergesagten Werte eines Regressionsmodells "
            "die tatsächlichen Datenpunkte annähern. Sie gibt einen Hinweis auf "
            "die Güte der Anpassung des Modells."
        ),
        zh=(
            "R2 分数（决定系数）衡量回归模型的预测值与实际数据点的吻合程度，"
            "反映模型的拟合优度。"
        ),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        pred_values: "np.ndarray",
    ) -> float:
        """Calculate the R2 score between true values and predicted values.

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
            R2 score between true values and predicted values
        """
        from sklearn.metrics import r2_score

        true_values, pred_values = prepare_to_metric(true_values, pred_values)
        return r2_score(true_values, pred_values)
