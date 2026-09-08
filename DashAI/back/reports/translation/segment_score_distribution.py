"""Distribution of per segment translation scores report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.translation.per_segment_comparison import (
    per_segment_scores,
)


class SegmentScoreDistributionSchema(BaseSchema):
    """Schema that configures the segment score distribution report."""

    bins: schema_field(
        int_field(ge=5, le=200),
        placeholder=20,
        description=MultilingualString(
            en="Number of bins used to bucket the per segment scores.",
            es=(
                "Número de contenedores usados para agrupar las puntuaciones "
                "por segmento."
            ),
            pt=(
                "Número de compartimentos usados para agrupar as pontuações "
                "por segmento."
            ),
            de="Anzahl der Klassen zur Gruppierung der Segment-Scores.",
            zh="用于划分每片段分数的分箱数量。",
        ),
        alias=MultilingualString(
            en="Bins", es="Contenedores", pt="Compartimentos", de="Klassen", zh="分箱数"
        ),
    )  # type: ignore


class SegmentScoreDistribution(BaseReport):
    """Distribution of the sentence level BLEU scores across segments.

    The corpus BLEU metric is a single point on this histogram; the histogram
    is the shape of the quality. A split whose scores cluster high with a
    handful near zero contains a few broken translations among otherwise good
    ones, while a wide flat distribution means quality is uniformly mediocre —
    a different problem to solve, and one the aggregate cannot tell apart.
    """

    SCHEMA = SegmentScoreDistributionSchema
    COMPATIBLE_COMPONENTS = ["TranslationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Segment Score Distribution",
        es="Distribución de Puntuaciones por Segmento",
        pt="Distribuição de Pontuações por Segmento",
        de="Verteilung der Segment-Scores",
        zh="片段分数分布",
    )
    DESCRIPTION: str = MultilingualString(
        en="Histogram of the per segment BLEU scores, with the mean marked.",
        es=("Histograma de las puntuaciones BLEU por segmento, con la media marcada."),
        pt=("Histograma das pontuações BLEU por segmento, com a média marcada."),
        de=("Histogramm der BLEU-Scores je Segment, mit markiertem Mittelwert."),
        zh="每个片段的 BLEU 分数直方图，并标注平均值。",
    )
    COLOR: str = "#AB47BC"
    ICON: str = "BarChart"

    def __init__(self, bins: int = 20, **kwargs) -> None:
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
        """Build the segment score distribution histogram.

        Parameters
        ----------
        y_true : array_like
            Reference translations, one per row.
        y_pred : array_like
            The model's translations for the same rows.
        class_names : Optional[List[str]]
            Unused; always None for translation.

        Returns
        -------
        List[Artifact]
            A single histogram figure with a mean reference line.
        """
        import plotly.graph_objects as go

        scores = per_segment_scores(y_true, y_pred)

        figure = go.Figure(
            go.Histogram(
                x=scores,
                nbinsx=int(self.bins),
                marker={"color": "#ab47bc"},
                name="Scores",
            )
        )
        figure.add_vline(
            x=sum(scores) / len(scores),
            line_dash="dash",
            line_color="#9e9e9e",
        )
        figure.update_layout(
            title=(
                f"Segment score distribution (mean {sum(scores) / len(scores):.4g})"
            ),
            xaxis_title="Sentence BLEU",
            yaxis_title="Count",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Segment score distribution")]
