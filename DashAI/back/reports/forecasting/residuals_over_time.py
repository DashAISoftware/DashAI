"""Residuals against the observation index report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.regression.predicted_vs_actual import flat_predictions


class ResidualsOverTime(BaseReport):
    """Residual against observation index, with the zero line.

    The residual plot used by regression scatters residuals against the
    predicted value; forecasting keeps that diagnostic but plots against
    time, because time is where the error pattern lives. A band that widens
    to the right means the forecast error compounds over the horizon, a
    band that drifts off zero means the model is systematically behind or
    ahead of the series, and a repeating pattern means a missed seasonality.
    """

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Residuals Over Time",
        es="Residuos en el Tiempo",
        pt="Resíduos ao Longo do Tempo",
        de="Residuen über die Zeit",
        zh="残差随时间变化",
    )
    DESCRIPTION: str = MultilingualString(
        en="Residual against observation index; reveals drift and missed seasonality.",
        es=(
            "Residuo contra índice de observación; revela deriva y estacionalidad "
            "omitida."
        ),
        pt=(
            "Resíduo contra índice de observação; revela deriva e sazonalidade perdida."
        ),
        de=(
            "Residuum gegen Beobachtungsindex; zeigt Drift und übersehene Saisonalität."
        ),
        zh="残差与观测序号的对应关系；可揭示漂移与遗漏的季节性。",
    )
    COLOR: str = "#EF5350"
    ICON: str = "Timeline"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the residuals against observation index scatter.

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
            A single scatter figure with the zero reference line.
        """
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        residuals = truth - predictions
        observations = list(range(len(truth)))

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[observations[0], observations[-1]],
                y=[0, 0],
                mode="lines",
                name="Zero error",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=observations,
                y=residuals.tolist(),
                mode="markers",
                name="Residuals",
                marker={"size": 6, "opacity": 0.7, "color": "#ef5350"},
            )
        )
        figure.update_layout(
            title="Residuals over time",
            xaxis_title="Observation",
            yaxis_title="Residual (actual minus forecast)",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Residuals over time")]
