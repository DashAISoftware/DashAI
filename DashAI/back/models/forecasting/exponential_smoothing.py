from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.forecasting.base_forecasting_model import ForecastingModel

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

COMPONENTS = ["none", "add", "mul"]


class ExponentialSmoothingSchema(BaseSchema):
    """Schema that configures the exponential smoothing model."""

    trend: schema_field(
        enum_field(COMPONENTS),
        "none",
        description=MultilingualString(
            en=(
                "Whether the series drifts steadily up or down. 'add' for a "
                "trend of roughly constant size, 'mul' for one that grows with "
                "the level, 'none' for a series with no direction."
            ),
            es=(
                "Si la serie deriva de forma sostenida hacia arriba o abajo. "
                "'add' para una tendencia de tamano aproximadamente constante, "
                "'mul' para una que crece con el nivel, 'none' para una serie "
                "sin direccion."
            ),
            pt=(
                "Se a serie deriva de forma sustentada para cima ou para "
                "baixo. 'add' para uma tendencia de tamanho aproximadamente "
                "constante, 'mul' para uma que cresce com o nivel, 'none' para "
                "uma serie sem direcao."
            ),
            de=(
                "Ob die Reihe stetig steigt oder faellt. 'add' fuer einen "
                "Trend etwa gleichbleibender Groesse, 'mul' fuer einen, der mit "
                "dem Niveau waechst, 'none' fuer eine Reihe ohne Richtung."
            ),
            zh=(
                "序列是否持续上升或下降。'add' 表示幅度大致恒定的趋势，"
                "'mul' 表示随水平增长的趋势，'none' 表示没有方向的序列。"
            ),
        ),
        alias=MultilingualString(
            en="Trend", es="Tendencia", pt="Tendencia", de="Trend", zh="趋势"
        ),
    )  # type: ignore
    seasonal: schema_field(
        enum_field(COMPONENTS),
        "none",
        description=MultilingualString(
            en=(
                "Whether a pattern repeats every season. 'add' when the swing "
                "is about the same size each cycle, 'mul' when it grows with "
                "the level. Needs a season length above 1."
            ),
            es=(
                "Si un patron se repite cada estacion. 'add' cuando la "
                "oscilacion tiene un tamano similar en cada ciclo, 'mul' "
                "cuando crece con el nivel. Requiere una longitud de estacion "
                "mayor que 1."
            ),
            pt=(
                "Se um padrao se repete a cada estacao. 'add' quando a "
                "oscilacao tem tamanho semelhante em cada ciclo, 'mul' quando "
                "cresce com o nivel. Requer um comprimento de estacao maior "
                "que 1."
            ),
            de=(
                "Ob sich ein Muster jede Saison wiederholt. 'add', wenn der "
                "Ausschlag pro Zyklus etwa gleich gross ist, 'mul', wenn er mit "
                "dem Niveau waechst. Erfordert eine Saisonlaenge groesser 1."
            ),
            zh=(
                "是否存在每个季节重复的模式。'add' 表示每个周期波动幅度相近，"
                "'mul' 表示波动随水平增长。需要季节长度大于 1。"
            ),
        ),
        alias=MultilingualString(
            en="Seasonal",
            es="Estacional",
            pt="Sazonal",
            de="Saisonal",
            zh="季节性",
        ),
    )  # type: ignore
    season_length: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 2,
            "upper_bound": 12,
        },
        description=MultilingualString(
            en=(
                "How many observations make up one full cycle: 12 for monthly "
                "data repeating yearly, 7 for daily data repeating weekly. "
                "Only used when a seasonal component is selected."
            ),
            es=(
                "Cuantas observaciones forman un ciclo completo: 12 para datos "
                "mensuales que se repiten cada ano, 7 para datos diarios que se "
                "repiten cada semana. Solo se usa si se elige un componente "
                "estacional."
            ),
            pt=(
                "Quantas observacoes formam um ciclo completo: 12 para dados "
                "mensais que se repetem a cada ano, 7 para dados diarios que se "
                "repetem a cada semana. Usado apenas quando ha componente "
                "sazonal."
            ),
            de=(
                "Wie viele Beobachtungen einen vollen Zyklus bilden: 12 fuer "
                "monatliche Daten mit jaehrlicher Wiederholung, 7 fuer "
                "taegliche mit woechentlicher. Nur bei gewaehlter saisonaler "
                "Komponente verwendet."
            ),
            zh=(
                "一个完整周期包含多少个观测值：月度数据按年重复为 12，"
                "日度数据按周重复为 7。仅在选择季节性成分时使用。"
            ),
        ),
        alias=MultilingualString(
            en="Season length",
            es="Longitud de estacion",
            pt="Comprimento da estacao",
            de="Saisonlaenge",
            zh="季节长度",
        ),
    )  # type: ignore


class ExponentialSmoothing(ForecastingModel):
    """Forecast from a weighted average that favours recent observations.

    Exponential smoothing tracks the level of a series by averaging its past,
    weighting each observation less the older it is. Optional trend and
    seasonal components extend that to series which drift or repeat, which
    together make up the Holt-Winters method.

    Where ARIMA models a series through its correlations, this models it
    through its structure: level, direction, and repeating pattern. That makes
    it the better first choice when a series visibly has a season, and it is
    usually easier to configure, since the three components are things you can
    see in a plot rather than orders you have to search for.

    Additive components suit a swing of roughly constant size; multiplicative
    ones suit a swing that grows as the series does. A seasonal component needs
    a season length above 1 and at least two full cycles of history.

    References
    ----------
    - [1] https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html
    - [2] https://otexts.com/fpp3/expsmooth.html
    """

    SCHEMA = ExponentialSmoothingSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Forecasts from a weighted average that favours recent "
            "observations, with optional trend and seasonal components. The "
            "Holt-Winters method, and the better first choice for a series "
            "with a visible season."
        ),
        es=(
            "Pronostica a partir de un promedio ponderado que favorece las "
            "observaciones recientes, con componentes opcionales de tendencia "
            "y estacionalidad. El metodo Holt-Winters, y la mejor primera "
            "opcion para una serie con estacionalidad visible."
        ),
        pt=(
            "Preve a partir de uma media ponderada que favorece as observacoes "
            "recentes, com componentes opcionais de tendencia e sazonalidade. "
            "O metodo Holt-Winters, e a melhor primeira escolha para uma serie "
            "com sazonalidade visivel."
        ),
        de=(
            "Prognostiziert aus einem gewichteten Mittel, das juengere "
            "Beobachtungen bevorzugt, mit optionalen Trend- und "
            "Saisonkomponenten. Das Holt-Winters-Verfahren und die bessere "
            "erste Wahl fuer eine Reihe mit sichtbarer Saison."
        ),
        zh=(
            "基于偏重近期观测的加权平均进行预测，可选加入趋势和季节性成分。"
            "即 Holt-Winters 方法，是具有明显季节性的序列的更佳首选。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Exponential Smoothing",
        es="Suavizado Exponencial",
        pt="Suavizacao Exponencial",
        de="Exponentielle Glaettung",
        zh="指数平滑",
    )

    def __init__(
        self,
        trend: str = "none",
        seasonal: str = "none",
        season_length: int = 1,
        **kwargs,
    ):
        """Initialise the model with its structural components.

        Parameters
        ----------
        trend : str
            One of ``"none"``, ``"add"`` or ``"mul"``.
        seasonal : str
            One of ``"none"``, ``"add"`` or ``"mul"``.
        season_length : int
            Observations per full cycle, used only with a seasonal component.
        **kwargs
            Ignored, accepted for consistency with the other models.

        Raises
        ------
        ValueError
            If a component is not one of the supported values, or a seasonal
            component was asked for without a season length above 1.
        """
        super().__init__(**kwargs)
        for name, value in (("trend", trend), ("seasonal", seasonal)):
            if value not in COMPONENTS:
                raise ValueError(
                    f"'{name}' must be one of {COMPONENTS}, got '{value}'."
                )
        if seasonal != "none" and season_length < 2:
            raise ValueError(
                "A seasonal component needs a season length of at least 2, got "
                f"{season_length}. A season of 1 would repeat every "
                "observation, which is not a season."
            )

        self.trend = trend
        self.seasonal = seasonal
        self.season_length = season_length
        self._result = None

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "ExponentialSmoothing":
        """Fit the smoothing model to the series.

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
        ExponentialSmoothing
            The fitted model.

        Raises
        ------
        ValueError
            If a seasonal component was asked for and the series is shorter
            than two full cycles.
        """
        import warnings

        from statsmodels.tsa.holtwinters import (
            ExponentialSmoothing as _ExponentialSmoothing,
        )

        series = self._series(y_train)
        seasonal = None if self.seasonal == "none" else self.seasonal
        trend = None if self.trend == "none" else self.trend

        if seasonal is not None and len(series) < 2 * self.season_length:
            raise ValueError(
                f"A seasonal component with a season of {self.season_length} "
                f"needs at least {2 * self.season_length} observations to see "
                f"the pattern twice, but the series has {len(series)}."
            )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._result = _ExponentialSmoothing(
                series,
                trend=trend,
                seasonal=seasonal,
                seasonal_periods=self.season_length if seasonal else None,
            ).fit()

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
        return self._result.forecast(steps)
