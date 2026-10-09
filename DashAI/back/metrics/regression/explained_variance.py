"""DashAI Explained Variance regression metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ExplainedVariance(RegressionMetric):
    """Proportion of the target variance explained by the regression model.

    The Explained Variance Score quantifies how much of the variability in
    the dependent variable is captured by the model's predictions. It is
    closely related to R², but does not penalise for a systematic bias
    (constant offset) in the predictions. A model with a fixed offset can
    achieve a high Explained Variance score while having a lower R².

    ::

        EV(y, ŷ) = 1 - Var(y - ŷ) / Var(y)

    Range: (-∞, 1]. A score of 1.0 means the model explains all variance;
    0.0 means it performs no better than predicting the mean; negative values
    indicate that the model performs worse than the mean predictor.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.explained_variance_score.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Explained Variance measures the proportion of the variance in the "
            "dependent variable that is predictable from the independent variables "
            "in a regression model. It provides an indication of how well the model "
            "captures the variability of the data."
        ),
        es=(
            "La Varianza Explicada mide la proporción de la varianza en la "
            "variable dependiente que es predecible a partir de las variables "
            "independientes "
            "en un modelo de regresión. Indica qué tan bien el modelo "
            "captura la variabilidad de los datos."
        ),
        pt=(
            "A Variância Explicada mede a proporção da variância na "
            "variável dependente que é previsível a partir das variáveis "
            "independentes "
            "em um modelo de regressão. Indica quão bem o modelo "
            "captura a variabilidade dos dados."
        ),
        de=(
            "Erklärte Varianz misst den Anteil der Varianz in der "
            "abhängigen Variable, der aus den unabhängigen Variablen "
            "in einem Regressionsmodell vorhersagbar ist. Sie gibt an, wie gut das "
            "Modell "
            "die Variabilität der Daten erfasst."
        ),
        zh=(
            "解释方差衡量回归模型中因变量的方差可由自变量预测的比例，"
            "反映模型捕获数据变异性的能力。"
        ),
    )

    MAXIMIZE = True

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        predicted_values: "np.ndarray",
    ) -> float:
        """Calculate the Explained Variance between true values and predicted values.

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
            Explained Variance score between true values and predicted values
        """
        from sklearn.metrics import explained_variance_score

        true_values, pred_values = prepare_to_metric(true_values, predicted_values)
        return explained_variance_score(true_values, pred_values)
