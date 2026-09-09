"""Residual distribution report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.regression.predicted_vs_actual import flat_predictions


class ResidualHistogramSchema(BaseSchema):
    """Schema that configures the residual histogram."""

    bins: schema_field(
        int_field(ge=5, le=200),
        placeholder=30,
        description=MultilingualString(
            en="Number of bins used to bucket the residuals.",
            es="Número de contenedores usados para agrupar los residuos.",
            pt="Número de compartimentos usados para agrupar os resíduos.",
            de="Anzahl der Klassen zur Gruppierung der Residuen.",
            zh="用于划分残差的分箱数量。",
        ),
        alias=MultilingualString(
            en="Bins", es="Contenedores", pt="Compartimentos", de="Klassen", zh="分箱数"
        ),
    )  # type: ignore


class ResidualHistogram(BaseReport):
    """Distribution of the residuals, with the zero line marked.

    Shows the shape of the error rather than its magnitude. Residuals should
    centre on zero and fall away symmetrically; a shifted centre means constant
    bias, a long tail on one side means the model fails asymmetrically, and two
    peaks usually mean a subpopulation the model treats as one group.
    """

    SCHEMA = ResidualHistogramSchema
    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Residual Histogram",
        es="Histograma de Residuos",
        pt="Histograma de Resíduos",
        de="Residuen-Histogramm",
        zh="残差直方图",
    )
    DESCRIPTION: str = MultilingualString(
        en="Distribution of the errors; should centre on zero and look symmetric.",
        es=(
            "Distribución de los errores; debería centrarse en cero y verse simétrica."
        ),
        pt=("Distribuição dos erros; deve centrar-se em zero e parecer simétrica."),
        de=("Verteilung der Fehler; sollte bei null zentriert und symmetrisch sein."),
        zh="误差的分布；应以零为中心且大致对称。",
    )
    COLOR: str = "#FFA726"
    ICON: str = "BarChart"

    def __init__(self, bins: int = 30, **kwargs) -> None:
        """Initialise the report.

        Parameters
        ----------
        bins : int
            Number of histogram bins.
        **kwargs : dict
            Ignored; accepted so unknown stored parameters do not break loading.
        """
        self.bins = bins

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the residual histogram.

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
            A single histogram figure with a zero reference line.
        """
        import plotly.graph_objects as go

        truth, predictions = flat_predictions(y_true, y_pred)
        residuals = truth - predictions

        figure = go.Figure(
            go.Histogram(
                x=residuals.tolist(),
                nbinsx=int(self.bins),
                marker={"color": "#ffa726"},
                name="Residuals",
            )
        )
        figure.add_vline(x=0, line_dash="dash", line_color="#9e9e9e")
        figure.update_layout(
            title=(
                f"Residual distribution (mean {residuals.mean():.4g}, "
                f"std {residuals.std():.4g})"
            ),
            xaxis_title="Residual (actual minus predicted)",
            yaxis_title="Count",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Residual histogram")]
