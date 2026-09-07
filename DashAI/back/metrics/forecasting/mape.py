"""DashAI MAPE forecasting metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.regression_metric import RegressionMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MAPE(RegressionMetric):
    """Average error as a percentage of the true value.

    Mean Absolute Percentage Error expresses each error relative to the value
    it missed, so a forecast can be judged without knowing the scale of the
    series. That is what makes it the usual way to compare a forecast across
    products, regions or periods whose magnitudes differ by orders of
    magnitude, where an absolute error in units says nothing on its own.

    ::

        MAPE(y, y') = 100 / N  ·  sum |yi - y'i| / |yi|

    Range: [0, +inf), lower is better.

    The formula divides by the true value, so it is undefined wherever that
    value is zero. Those rows are left out of the average rather than being
    allowed to produce an infinity that would swallow the whole score, and a
    series that is zero throughout has no defined MAPE at all, which is
    reported as ``nan``. Prefer :class:`SMAPE` on series that reach zero.

    MAPE is also asymmetric: it penalises a forecast that is too high more
    heavily than one that is too low by the same amount, since the denominator
    stays fixed while the error does not.

    References
    ----------
    - [1] https://otexts.com/fpp3/accuracy.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Average error as a percentage of the true value, so forecasts can "
            "be compared across series of different sizes. Undefined where the "
            "true value is zero, and those rows are skipped."
        ),
        es=(
            "Error promedio como porcentaje del valor real, lo que permite "
            "comparar pronosticos entre series de distinta magnitud. No esta "
            "definido cuando el valor real es cero, y esas filas se omiten."
        ),
        pt=(
            "Erro medio como porcentagem do valor real, permitindo comparar "
            "previsoes entre series de magnitudes diferentes. Indefinido "
            "quando o valor real e zero, e essas linhas sao ignoradas."
        ),
        de=(
            "Durchschnittlicher Fehler als Prozentsatz des wahren Wertes, "
            "sodass Prognosen ueber unterschiedlich grosse Reihen hinweg "
            "vergleichbar sind. Undefiniert, wo der wahre Wert null ist; "
            "solche Zeilen werden uebersprungen."
        ),
        zh=(
            "以真实值的百分比表示的平均误差，便于比较不同量级序列的预测效果。"
            "当真实值为零时无定义，这些行会被跳过。"
        ),
    )

    @staticmethod
    def score(
        true_values: "DashAIDataset",
        pred_values: "np.ndarray",
    ) -> float:
        """Calculate the MAPE between true values and predicted values.

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
            MAPE as a percentage. ``nan`` when every true value is zero, since
            no row of such a series has a defined percentage error.
        """
        import numpy as np

        true_values, pred_values = prepare_to_metric(true_values, pred_values)

        defined = true_values != 0
        if not defined.any():
            return float("nan")

        errors = np.abs(true_values[defined] - pred_values[defined])
        return float(100 * np.mean(errors / np.abs(true_values[defined])))
