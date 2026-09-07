from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema, optimizer_int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.forecasting.base_forecasting_model import ForecastingModel

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def _order_field(letter: str, meaning: MultilingualString, upper: int):
    """Build one of the three ARIMA order fields.

    The three share a shape and differ only in what they mean, so writing them
    out separately would be three copies of the same twelve lines.

    Parameters
    ----------
    letter : str
        The conventional name of the term, ``p``, ``d`` or ``q``.
    meaning : MultilingualString
        The description shown to the user.
    upper : int
        Upper bound offered when the value is optimized.

    Returns
    -------
    Any
        A configured schema field.
    """
    return schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 1 if letter != "q" else 0,
            "lower_bound": 0,
            "upper_bound": upper,
        },
        description=meaning,
        alias=MultilingualString(
            en=f"Order {letter}",
            es=f"Orden {letter}",
            pt=f"Ordem {letter}",
            de=f"Ordnung {letter}",
            zh=f"阶数 {letter}",
        ),
    )


class ARIMASchema(BaseSchema):
    """Schema that configures the ARIMA model."""

    p: _order_field(
        "p",
        MultilingualString(
            en=(
                "How many past values the forecast is a weighted sum of, the "
                "autoregressive order."
            ),
            es=(
                "De cuantos valores pasados es suma ponderada el pronostico, "
                "el orden autorregresivo."
            ),
            pt=(
                "De quantos valores passados a previsao e soma ponderada, a "
                "ordem autorregressiva."
            ),
            de=(
                "Aus wie vielen vergangenen Werten die Prognose gewichtet "
                "gebildet wird, die autoregressive Ordnung."
            ),
            zh="预测由多少个过去的值加权求和得到，即自回归阶数。",
        ),
        5,
    )  # type: ignore
    d: _order_field(
        "d",
        MultilingualString(
            en=(
                "How many times to difference the series before modelling it. "
                "1 removes a straight trend, 0 suits a series that already "
                "hovers around a fixed level."
            ),
            es=(
                "Cuantas veces diferenciar la serie antes de modelarla. 1 "
                "elimina una tendencia lineal, 0 sirve para una serie que ya "
                "oscila alrededor de un nivel fijo."
            ),
            pt=(
                "Quantas vezes diferenciar a serie antes de modela-la. 1 "
                "remove uma tendencia linear, 0 serve para uma serie que ja "
                "oscila em torno de um nivel fixo."
            ),
            de=(
                "Wie oft die Reihe vor der Modellierung differenziert wird. 1 "
                "entfernt einen linearen Trend, 0 passt zu einer Reihe, die "
                "bereits um ein festes Niveau schwankt."
            ),
            zh=(
                "建模前对序列做几次差分。1 可去除线性趋势，"
                "0 适用于已经围绕固定水平波动的序列。"
            ),
        ),
        2,
    )  # type: ignore
    q: _order_field(
        "q",
        MultilingualString(
            en=(
                "How many past forecast errors feed into the next forecast, "
                "the moving average order."
            ),
            es=(
                "Cuantos errores de pronostico pasados alimentan el siguiente "
                "pronostico, el orden de media movil."
            ),
            pt=(
                "Quantos erros de previsao passados alimentam a proxima "
                "previsao, a ordem de media movel."
            ),
            de=(
                "Wie viele vergangene Prognosefehler in die naechste Prognose "
                "einfliessen, die Ordnung des gleitenden Mittels."
            ),
            zh="有多少个过去的预测误差参与下一次预测，即移动平均阶数。",
        ),
        5,
    )  # type: ignore


class ARIMA(ForecastingModel):
    """Model a series as its own past values plus its own past errors.

    ARIMA combines three ideas, one per order. The autoregressive part (``p``)
    makes the forecast a weighted sum of recent values. The differencing part
    (``d``) subtracts consecutive observations until what is left has no trend,
    which is what lets the other two parts assume a stable level. The moving
    average part (``q``) lets recent forecast errors feed back in.

    It is the standard reference model for a series without a strong seasonal
    pattern. For seasonality, prefer :class:`ExponentialSmoothing` with a
    seasonal component, since seasonal ARIMA would need three more orders that
    this wrapper does not expose.

    The orders are not chosen automatically. ``d = 1`` suits a series that
    trends, ``d = 0`` one that hovers around a level, and the DashAI optimizer
    can search all three when told to.

    References
    ----------
    - [1] https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html
    - [2] https://otexts.com/fpp3/arima.html
    """

    SCHEMA = ARIMASchema
    DESCRIPTION = MultilingualString(
        en=(
            "Models a series from its own past values and past errors, after "
            "differencing away any trend. The standard reference model for a "
            "series without strong seasonality."
        ),
        es=(
            "Modela una serie a partir de sus propios valores y errores "
            "pasados, tras eliminar la tendencia por diferenciacion. El modelo "
            "de referencia estandar para series sin estacionalidad marcada."
        ),
        pt=(
            "Modela uma serie a partir dos seus proprios valores e erros "
            "passados, apos remover a tendencia por diferenciacao. O modelo de "
            "referencia padrao para series sem sazonalidade forte."
        ),
        de=(
            "Modelliert eine Reihe aus ihren eigenen vergangenen Werten und "
            "Fehlern, nachdem ein Trend wegdifferenziert wurde. Das "
            "Standardreferenzmodell fuer Reihen ohne starke Saisonalitaet."
        ),
        zh=(
            "在通过差分消除趋势后，用序列自身的历史值和历史误差建模。"
            "这是无明显季节性序列的标准参考模型。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="ARIMA", es="ARIMA", pt="ARIMA", de="ARIMA", zh="ARIMA"
    )

    def __init__(self, p: int = 1, d: int = 1, q: int = 0, **kwargs):
        """Initialise the model with its three orders.

        Parameters
        ----------
        p : int
            Autoregressive order.
        d : int
            Number of differences.
        q : int
            Moving average order.
        **kwargs
            Ignored, accepted for consistency with the other models.
        """
        super().__init__(**kwargs)
        self.p = p
        self.d = d
        self.q = q
        self._result = None

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "ARIMA":
        """Fit the ARIMA model to the series.

        Parameters
        ----------
        x_train : DashAIDataset
            The date column. statsmodels is given the values in order and the
            spacing is assumed regular; the dates are kept so a later
            partition can be forecast at its own dates.
        y_train : DashAIDataset
            The series to forecast.
        x_validation : DashAIDataset, optional
            Unused.
        y_validation : DashAIDataset, optional
            Unused.

        Returns
        -------
        ARIMA
            The fitted model.

        Raises
        ------
        ValueError
            If the series is too short for the requested orders.
        """
        import warnings

        from statsmodels.tsa.arima.model import ARIMA as _ARIMA

        series = self._series(y_train)
        if len(series) <= self.p + self.d + self.q:
            raise ValueError(
                f"An ARIMA({self.p},{self.d},{self.q}) needs more than "
                f"{self.p + self.d + self.q} observations, but the series has "
                f"{len(series)}."
            )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._result = _ARIMA(series, order=(self.p, self.d, self.q)).fit()

        self._history = list(series)
        self._remember_dates(x_train)
        self._fitted = True
        return self

    def _forecast(self, steps: int) -> "np.ndarray":
        """Forecast the next ``steps`` periods after the end of the history.

        Parameters
        ----------
        steps : int
            How many periods to forecast.

        Returns
        -------
        np.ndarray
            One value per period, in order.
        """
        return self._result.forecast(steps=steps)
