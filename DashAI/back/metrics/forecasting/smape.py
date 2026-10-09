"""DashAI sMAPE forecasting metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SMAPE(RegressionMetric):
    """Percentage error measured against the size of both values.

    Symmetric Mean Absolute Percentage Error divides each error by the average
    of the true and predicted values rather than by the true value alone. That
    small change fixes the two things that make :class:`MAPE` awkward on real
    series: it stays defined when the truth is zero, and it does not punish
    over-forecasting more harshly than under-forecasting.

    ::

        sMAPE(y, y') = 100 / N  ·  sum 2 |yi - y'i| / (|yi| + |y'i|)

    Range: [0, 200], lower is better. The ceiling is reached when a value and
    its forecast have nothing in common, for example predicting a non-zero
    number where the truth is zero, which is exactly the case MAPE cannot
    score at all.

    A row where the true value and the forecast are both zero is counted as no
    error rather than as an undefined ratio, since a forecast of nothing that
    turned out to be nothing is right.

    References
    ----------
    - [1] https://otexts.com/fpp3/accuracy.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Percentage error measured against the average of the true and "
            "predicted values. Stays defined when the true value is zero and "
            "treats over and under forecasting alike, unlike MAPE."
        ),
        es=(
            "Error porcentual medido respecto al promedio del valor real y el "
            "predicho. Sigue definido cuando el valor real es cero y trata "
            "igual la sobreestimacion y la subestimacion, a diferencia de MAPE."
        ),
        pt=(
            "Erro percentual medido em relacao a media do valor real e do "
            "previsto. Permanece definido quando o valor real e zero e trata "
            "igualmente super e subprevisao, ao contrario do MAPE."
        ),
        de=(
            "Prozentualer Fehler, gemessen am Mittel aus wahrem und "
            "vorhergesagtem Wert. Bleibt definiert, wenn der wahre Wert null "
            "ist, und behandelt Ueber- und Unterschaetzung gleich, anders als "
            "MAPE."
        ),
        zh=(
            "以真实值与预测值的平均数为基准衡量的百分比误差。"
            "与 MAPE 不同，它在真实值为零时仍有定义，且对高估和低估一视同仁。"
        ),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        pred_values: "np.ndarray",
    ) -> float:
        """Calculate the sMAPE between true values and predicted values.

        Parameters
        ----------
        true_values : DashAIDataset
            A DashAI dataset with true values.
        pred_values : np.ndarray
            A one-dimensional array with the predicted values for each
            instance.

        Returns
        -------
        float
            sMAPE as a percentage between 0 and 200.
        """
        import numpy as np

        true_values, pred_values = prepare_to_metric(true_values, pred_values)

        scale = np.abs(true_values) + np.abs(pred_values)
        errors = np.abs(true_values - pred_values)

        # Both values zero means the forecast was right, so the ratio is 0
        # rather than the 0/0 that dividing would produce.
        ratios = np.divide(
            2 * errors, scale, out=np.zeros_like(scale, dtype=float), where=scale != 0
        )
        return float(100 * np.mean(ratios))
