"""Residual autocorrelation report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport, ReportError
from DashAI.back.reports.regression.predicted_vs_actual import flat_predictions


class ResidualAutocorrelationSchema(BaseSchema):
    """Schema that configures the residual autocorrelation report."""

    max_lag: schema_field(
        int_field(ge=1, le=200),
        placeholder=20,
        description=MultilingualString(
            en="Number of lags to plot the autocorrelation for.",
            es="Número de rezagos para los cuales graficar la autocorrelación.",
            pt="Número de defasagens para as quais plotar a autocorrelação.",
            de="Anzahl der Lags, für die die Autokorrelation dargestellt wird.",
            zh="要绘制自相关的滞后阶数。",
        ),
        alias=MultilingualString(
            en="Max lag",
            es="Rezago máximo",
            pt="Defasagem máxima",
            de="Maximale Verzögerung",
            zh="最大滞后阶数",
        ),
    )  # type: ignore


class ResidualAutocorrelation(BaseReport):
    """Autocorrelation of the residuals against the number of lags.

    A good forecast leaves residuals that look like noise: each error carries
    no information about the next. Autocorrelation measures exactly that, so
    a bar above the confidence band means the model left structure behind —
    neighbouring periods are wrong in the same direction, which a tuned
    model would have learned. Lags rising and falling smoothly usually mean
    a missed trend or seasonality, while a single spike means a specific
    lag that was never modelled.
    """

    SCHEMA = ResidualAutocorrelationSchema
    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Residual Autocorrelation",
        es="Autocorrelación de Residuos",
        pt="Autocorrelação dos Resíduos",
        de="Residuen-Autokorrelation",
        zh="残差自相关",
    )
    DESCRIPTION: str = MultilingualString(
        en="Autocorrelation of the residuals by lag, with confidence band.",
        es="Autocorrelación de los residuos por rezago, con banda de confianza.",
        pt=("Autocorrelação dos resíduos por defasagem, com banda de confiança."),
        de=("Autokorrelation der Residuen nach Lag, mit Konfidenzband."),
        zh="按滞后阶数计算的残差自相关，附置信带。",
    )
    COLOR: str = "#26A69A"
    ICON: str = "BarChart"

    def __init__(self, max_lag: int = 20, **kwargs) -> None:
        """Initialise the report.

        Parameters
        ----------
        max_lag : int
            Number of lags to plot the autocorrelation for.
        **kwargs : dict
            Ignored; accepted so unknown stored parameters do not break loading.
        """
        self.max_lag = max_lag

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the residual autocorrelation bar chart.

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
            A single bar figure with a confidence band around zero.

        Raises
        ------
        ReportError
            If the residuals are constant or there are not enough of them to
            estimate a single lag.
        """
        import numpy as np
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        residuals = truth - predictions

        if len(residuals) < 2:
            raise ReportError(
                "The partition holds too few rows to estimate autocorrelation."
            )

        centered = residuals - residuals.mean()
        denom = centered @ centered
        if denom == 0:
            raise ReportError(
                "The residuals are constant, so autocorrelation is undefined."
            )

        lags = range(1, min(int(self.max_lag), len(residuals) - 1) + 1)
        values = [(centered[k:] @ centered[:-k]) / denom for k in lags]

        figure = go.Figure()
        figure.add_trace(
            go.Bar(
                x=list(lags),
                y=values,
                name="Autocorrelation",
                marker={"color": "#26a69a"},
            )
        )

        band = 1.96 / np.sqrt(len(residuals))
        figure.add_trace(
            go.Scatter(
                x=[lags[0], lags[-1]],
                y=[band, band],
                mode="lines",
                name="Confidence band",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[lags[0], lags[-1]],
                y=[-band, -band],
                mode="lines",
                showlegend=False,
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.update_layout(
            title="Residual autocorrelation",
            xaxis_title="Lag",
            yaxis_title="Autocorrelation",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Residual autocorrelation")]
