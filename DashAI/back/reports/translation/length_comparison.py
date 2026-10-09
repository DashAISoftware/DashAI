"""Reference against translation length comparison report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.translation.per_segment_comparison import as_text_pairs


class LengthComparison(BaseReport):
    """Reference length against translation length, with the identity line.

    Translation metrics score content, not length, so a model can earn good
    BLEU while systematically truncating or padding its output. This plot
    shows that shape directly: points hugging the identity line translate
    with faithful lengths, a cloud consistently below the line means the
    model shortens its output, and a horizontal band at one length means it
    produces roughly the same size of translation regardless of input.
    """

    COMPATIBLE_COMPONENTS = ["TranslationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Length Comparison",
        es="Comparación de Longitudes",
        pt="Comparação de Comprimentos",
        de="Längenvergleich",
        zh="长度对比",
    )
    DESCRIPTION: str = MultilingualString(
        en="Reference length against translation length; reveals truncation.",
        es="Longitud de referencia contra traducción; revela truncamiento.",
        pt=("Comprimento de referência contra tradução; revela truncamento."),
        de=("Referenzlänge gegen Übersetzungslänge; zeigt Kürzung."),
        zh="参考文本长度与译文长度的对比；可揭示截断问题。",
    )
    COLOR: str = "#FFA726"
    ICON: str = "ScatterPlot"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the reference against translation length scatter.

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
            A single scatter figure with the identity reference line.
        """
        import plotly.graph_objects as go

        truth, hypothesis = as_text_pairs(y_true, y_pred)
        reference_lengths = [len(text) for text in truth]
        hypothesis_lengths = [len(text) for text in hypothesis]
        low = min(min(reference_lengths), min(hypothesis_lengths))
        high = max(max(reference_lengths), max(hypothesis_lengths))

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[low, high],
                y=[low, high],
                mode="lines",
                name="Perfect match",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=reference_lengths,
                y=hypothesis_lengths,
                mode="markers",
                name="Segments",
                marker={"size": 7, "opacity": 0.7, "color": "#ffa726"},
            )
        )
        figure.update_layout(
            title="Reference vs translation length",
            xaxis_title="Reference length (characters)",
            yaxis_title="Translation length (characters)",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Length comparison")]
