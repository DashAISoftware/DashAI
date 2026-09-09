from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.forecasting.base_forecasting_model import ForecastingModel

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class NaiveForecasterSchema(BaseSchema):
    """Schema for NaiveForecaster. It has nothing to configure."""


class NaiveForecaster(ForecastingModel):
    """Predict that the series stays where it last was.

    Every future value is forecast as the final observed value. There is
    nothing to fit and nothing to tune.

    Its worth is as a yardstick, not as a forecast. A model that cannot beat
    this one has found nothing in the data, and until now DashAI gave no way
    to check that. On a random walk it is provably the best possible forecast,
    which is precisely why beating it on real series is harder than people
    expect.

    References
    ----------
    - [1] https://otexts.com/fpp3/simple-methods.html
    """

    SCHEMA = NaiveForecasterSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Predicts that every future value equals the last observed one. "
            "The baseline any real forecasting model has to beat to be worth "
            "using."
        ),
        es=(
            "Predice que cada valor futuro es igual al ultimo observado. Es la "
            "linea base que cualquier modelo de pronostico real debe superar "
            "para valer la pena."
        ),
        pt=(
            "Preve que cada valor futuro e igual ao ultimo observado. E a "
            "linha de base que qualquer modelo de previsao real precisa "
            "superar para valer a pena."
        ),
        de=(
            "Sagt voraus, dass jeder zukuenftige Wert dem zuletzt beobachteten "
            "entspricht. Die Grundlinie, die jedes echte Prognosemodell "
            "schlagen muss, um sich zu lohnen."
        ),
        zh=(
            "预测每个未来值都等于最后一个观测值。"
            "这是任何真正的预测模型都必须超越的基准。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Naive Forecaster",
        es="Pronostico Ingenuo",
        pt="Previsao Ingenua",
        de="Naive Prognose",
        zh="朴素预测",
    )

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "NaiveForecaster":
        """Remember the last value of the series.

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
        NaiveForecaster
            The fitted model.

        Raises
        ------
        ValueError
            If the series is empty.
        """
        series = self._series(y_train)
        if len(series) == 0:
            raise ValueError("NaiveForecaster needs at least one observation.")

        self._history = list(series)
        self._last_value = float(series[-1])
        self._remember_dates(x_train)
        self._fitted = True
        return self

    def _forecast(self, steps: int) -> "np.ndarray":
        """Repeat the last observed value for every requested step.

        Parameters
        ----------
        steps : int
            How many periods to forecast.

        Returns
        -------
        np.ndarray
            The last observed value, repeated.
        """
        import numpy as np

        return np.full(steps, self._last_value, dtype=float)
