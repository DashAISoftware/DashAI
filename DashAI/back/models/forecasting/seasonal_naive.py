from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema, optimizer_int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.forecasting.base_forecasting_model import ForecastingModel

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SeasonalNaiveForecasterSchema(BaseSchema):
    """Schema that configures the seasonal naive forecaster."""

    season_length: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 12,
        },
        description=MultilingualString(
            en=(
                "How many observations make up one full cycle: 12 for monthly "
                "data repeating yearly, 7 for daily data repeating weekly. "
                "Leave it at 1 when the series has no season, which makes this "
                "the plain naive forecast."
            ),
            es=(
                "Cuantas observaciones forman un ciclo completo: 12 para datos "
                "mensuales que se repiten cada ano, 7 para datos diarios que se "
                "repiten cada semana. Dejar en 1 cuando la serie no tiene "
                "estacionalidad, lo que equivale al pronostico ingenuo simple."
            ),
            pt=(
                "Quantas observacoes formam um ciclo completo: 12 para dados "
                "mensais que se repetem a cada ano, 7 para dados diarios que se "
                "repetem a cada semana. Deixe em 1 quando a serie nao tem "
                "sazonalidade, o que equivale a previsao ingenua simples."
            ),
            de=(
                "Wie viele Beobachtungen einen vollen Zyklus bilden: 12 fuer "
                "monatliche Daten mit jaehrlicher Wiederholung, 7 fuer "
                "taegliche Daten mit woechentlicher. Bei 1 belassen, wenn die "
                "Reihe keine Saison hat, was der einfachen naiven Prognose "
                "entspricht."
            ),
            zh=(
                "一个完整周期包含多少个观测值：月度数据按年重复为 12，"
                "日度数据按周重复为 7。序列没有季节性时保持为 1，"
                "此时等同于普通的朴素预测。"
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


class SeasonalNaiveForecaster(ForecastingModel):
    """Predict that each season repeats the one before it.

    Every future value is forecast as the value one full season earlier, so a
    monthly series with ``season_length = 12`` predicts next January from last
    January.

    On anything with a strong repeating pattern this is a much harder baseline
    than the plain naive forecast, and a seasonal model that cannot beat it has
    learned nothing beyond the repetition. With ``season_length = 1`` it is
    exactly :class:`NaiveForecaster`.

    The season length is not inferred. Monthly data may repeat yearly or not
    repeat at all, and only someone who knows what the series measures can say
    which.

    References
    ----------
    - [1] https://otexts.com/fpp3/simple-methods.html
    """

    SCHEMA = SeasonalNaiveForecasterSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Predicts that each value repeats the one a full season earlier, "
            "for example next January from last January. A far harder baseline "
            "than the naive forecast on any series with a repeating pattern."
        ),
        es=(
            "Predice que cada valor repite el de una estacion completa antes, "
            "por ejemplo el proximo enero a partir del enero anterior. Una "
            "linea base mucho mas exigente que el pronostico ingenuo en "
            "cualquier serie con un patron repetitivo."
        ),
        pt=(
            "Preve que cada valor repete o de uma estacao completa antes, por "
            "exemplo o proximo janeiro a partir do janeiro anterior. Uma linha "
            "de base bem mais exigente que a previsao ingenua em qualquer "
            "serie com padrao repetitivo."
        ),
        de=(
            "Sagt voraus, dass sich jeder Wert von vor einer vollen Saison "
            "wiederholt, etwa der naechste Januar aus dem letzten Januar. Eine "
            "deutlich haertere Grundlinie als die naive Prognose bei jeder "
            "Reihe mit wiederkehrendem Muster."
        ),
        zh=(
            "预测每个值重复一个完整季节之前的值，例如用去年一月预测下个一月。"
            "对于任何具有重复模式的序列，这都是比朴素预测严格得多的基准。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Seasonal Naive Forecaster",
        es="Pronostico Ingenuo Estacional",
        pt="Previsao Ingenua Sazonal",
        de="Saisonale Naive Prognose",
        zh="季节性朴素预测",
    )

    def __init__(self, season_length: int = 1, **kwargs):
        """Initialise the forecaster with the length of one cycle.

        Parameters
        ----------
        season_length : int
            Observations per full cycle. 1 means no seasonality.
        **kwargs
            Ignored, accepted for consistency with the other models.

        Raises
        ------
        ValueError
            If ``season_length`` is less than 1.
        """
        super().__init__(**kwargs)
        if season_length < 1:
            raise ValueError(
                f"'season_length' must be at least 1, got {season_length}."
            )
        self.season_length = season_length

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "SeasonalNaiveForecaster":
        """Remember the most recent full season of the series.

        Parameters
        ----------
        x_train : DashAIDataset
            The date column, used to record where the training data ends so a
            later partition can be forecast at its own dates.
        y_train : DashAIDataset
            The series to forecast.
        x_validation : DashAIDataset, optional
            Unused.
        y_validation : DashAIDataset, optional
            Unused.

        Returns
        -------
        SeasonalNaiveForecaster
            The fitted model.

        Raises
        ------
        ValueError
            If the series is shorter than one season, since there would be no
            complete cycle to repeat.
        """
        series = self._series(y_train)
        if len(series) < self.season_length:
            raise ValueError(
                f"A season of {self.season_length} needs at least that many "
                f"observations to repeat, but the series has {len(series)}. "
                "Shorten the season length or supply more history."
            )

        self._history = list(series)
        self._last_season = [float(v) for v in series[-self.season_length :]]
        self._remember_dates(x_train)
        self._fitted = True
        return self

    def _forecast(self, steps: int) -> "np.ndarray":
        """Repeat the last full season out to the requested length.

        Parameters
        ----------
        steps : int
            How many periods to forecast.

        Returns
        -------
        np.ndarray
            The last observed season, tiled to the requested length.
        """
        import numpy as np

        return np.array(
            [self._last_season[i % self.season_length] for i in range(steps)],
            dtype=float,
        )
