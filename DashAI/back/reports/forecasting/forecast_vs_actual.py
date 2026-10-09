"""Forecast against actual values over the observation index."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.regression.predicted_vs_actual import flat_predictions


class ForecastVsActual(BaseReport):
    """Forecast and truth as two lines over the observation index.

    An error scalar says how far off the forecast is on average; this says
    *where*. A forecast that tracks well early and drifts later shows a model
    whose error compounds over the horizon, while a line that runs parallel
    but offset reveals a level bias that RMSE folds into the rest of the
    error. Row order is time order for a forecasting run, because the task
    sorts its rows by date before anything downstream reads them.
    """

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Forecast vs Actual",
        es="Pronóstico vs Real",
        pt="Previsão vs Real",
        de="Prognose gegen Tatsächlich",
        zh="预测值与实际值",
    )
    DESCRIPTION: str = MultilingualString(
        en="Forecast and truth as lines over time; reveals drift and bias.",
        es="Pronóstico y verdad como líneas en el tiempo; revela deriva y sesgo.",
        pt=("Previsão e verdade como linhas ao longo do tempo; revela deriva e viés."),
        de=(
            "Prognose und Wahrheit als Linien über die Zeit; zeigt Drift und "
            "Verzerrung."
        ),
        zh="随时间变化的预测值与真实值曲线；可揭示漂移和偏差。",
    )
    COLOR: str = "#42A5F5"
    ICON: str = "ShowChart"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the forecast against actual line plot.

        Parameters
        ----------
        y_true : ndarray
            Ground truth values of the series.
        y_pred : ndarray
            The model's forecast for the same points.
        class_names : Optional[List[str]]
            Unused; always None for forecasting.

        Returns
        -------
        List[Artifact]
            A single figure holding the truth and the forecast lines.
        """
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        observations = list(range(len(truth)))

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=observations,
                y=truth.tolist(),
                mode="lines",
                name="Actual",
                line={"width": 2, "color": "#42a5f5"},
            )
        )
        figure.add_trace(
            go.Scatter(
                x=observations,
                y=predictions.tolist(),
                mode="lines",
                name="Forecast",
                line={"width": 2, "color": "#ffa726", "dash": "dash"},
            )
        )
        figure.update_layout(
            title="Forecast vs actual",
            xaxis_title="Observation",
            yaxis_title="Value",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Forecast vs actual")]
