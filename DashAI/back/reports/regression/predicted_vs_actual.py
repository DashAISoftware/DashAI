"""Predicted against actual report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport


def flat_predictions(y_true, y_pred):
    """Flatten the truth and predictions into aligned 1D float arrays.

    Parameters
    ----------
    y_true : ndarray
        Ground truth values.
    y_pred : ndarray
        Model predictions.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        The truth and the predictions, both 1D and float typed.
    """
    import numpy as np

    return (
        np.asarray(y_true, dtype=float).ravel(),
        np.asarray(y_pred, dtype=float).ravel(),
    )


class PredictedVsActual(BaseReport):
    """Scatter of predicted against true values with the identity line.

    R squared and RMSE say how far off the model is on average; this says
    *where*. Points bending away from the identity line at one end reveal a
    model that is accurate in the middle of the range and biased at the
    extremes, which no single error scalar can express.
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Predicted vs Actual",
        es="Predicho vs Real",
        pt="Previsto vs Real",
        de="Vorhergesagt gegen Tatsächlich",
        zh="预测值与实际值",
    )
    DESCRIPTION: str = MultilingualString(
        en="Predictions against the truth, with the perfect prediction line.",
        es="Predicciones contra la verdad, con la línea de predicción perfecta.",
        pt="Previsões contra a verdade, com a linha de previsão perfeita.",
        de="Vorhersagen gegen die Wahrheit, mit der perfekten Vorhersagelinie.",
        zh="预测值与真实值的对比，附完美预测参考线。",
    )
    COLOR: str = "#42A5F5"
    ICON: str = "ScatterPlot"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the predicted against actual scatter.

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
            A single scatter figure with the identity reference line.
        """
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        low = float(min(truth.min(), predictions.min()))
        high = float(max(truth.max(), predictions.max()))

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[low, high],
                y=[low, high],
                mode="lines",
                name="Perfect prediction",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=truth.tolist(),
                y=predictions.tolist(),
                mode="markers",
                name="Predictions",
                marker={"size": 6, "opacity": 0.7, "color": "#42a5f5"},
            )
        )
        figure.update_layout(
            title="Predicted vs actual",
            xaxis_title="Actual",
            yaxis_title="Predicted",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Predicted vs actual")]
