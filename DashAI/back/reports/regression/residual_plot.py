"""Residual against predicted report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.regression.predicted_vs_actual import flat_predictions


class ResidualPlot(BaseReport):
    """Residual against predicted value, with the zero line.

    A well specified model leaves residuals scattered as a formless band around
    zero. Structure in this plot is a diagnosis: curvature means a missing
    nonlinear term, a widening fan means heteroscedasticity, and a residual
    band that drifts off zero means systematic bias over part of the range.
    An error scalar reports the size of these problems but not their shape.
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Residual Plot",
        es="Gráfico de Residuos",
        pt="Gráfico de Resíduos",
        de="Residuendiagramm",
        zh="残差图",
    )
    DESCRIPTION: str = MultilingualString(
        en="Residual against predicted value; reveals bias and heteroscedasticity.",
        es=("Residuo contra valor predicho; revela sesgo y heterocedasticidad."),
        pt=("Resíduo contra valor previsto; revela viés e heterocedasticidade."),
        de=(
            "Residuum gegen vorhergesagten Wert; zeigt Verzerrung und "
            "Heteroskedastizität."
        ),
        zh="残差与预测值的关系；可揭示偏差与异方差性。",
    )
    COLOR: str = "#EF5350"
    ICON: str = "BubbleChart"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the residual against predicted scatter.

        Parameters
        ----------
        y_true : ndarray
            Ground truth values.
        y_pred : ndarray
            Model predictions.
        class_names : Optional[List[str]]
            Unused; always None for regression.

        Returns
        -------
        List[Artifact]
            A single scatter figure with the zero reference line.
        """
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        residuals = truth - predictions

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[float(predictions.min()), float(predictions.max())],
                y=[0, 0],
                mode="lines",
                name="Zero error",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=predictions.tolist(),
                y=residuals.tolist(),
                mode="markers",
                name="Residuals",
                marker={"size": 6, "opacity": 0.7, "color": "#ef5350"},
            )
        )
        figure.update_layout(
            title="Residuals vs predicted",
            xaxis_title="Predicted",
            yaxis_title="Residual (actual minus predicted)",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Residual plot")]
