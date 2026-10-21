"""Counts of characters, words and sentences in text items."""

import re
import statistics
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.text_analysis_explorer import TextAnalysisExplorer
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

SENTENCE_END = re.compile(r"[.!?…]+(?=[\"'”’)\]]*(?:\s|$))")
TRAILING_END = re.compile(r"[.!?…]+(?:[\"'”’)\]]*$)")


def text_counts(value: str) -> Dict[str, int]:
    """Count the characters, words and sentences of one text.

    Parameters
    ----------
    value : str
        The text.

    Returns
    -------
    Dict[str, int]
        ``characters`` (without surrounding spaces), ``words`` and
        ``sentences``; a non empty text without a sentence end counts as one
        sentence.
    """
    stripped = value.strip()
    words = len(stripped.split())
    sentences = len(SENTENCE_END.findall(stripped))
    if stripped and not TRAILING_END.search(stripped):
        sentences += 1
    return {"characters": len(stripped), "words": words, "sentences": sentences}


class TextStatisticsExplorer(TextAnalysisExplorer):
    """Summarise the length of text items in characters, words and sentences.

    Shows the totals and per item averages in a table. On a document the
    words per item are also compared by element kind and the words are
    totalled by page; on a dataset the words per value are shown as a
    histogram.
    """

    SCHEMA = BaseExplorerSchema
    DISPLAY_NAME = MultilingualString(
        en="Text Statistics",
        es="Estadísticas de Texto",
        pt="Estatísticas de Texto",
        de="Textstatistik",
        zh="文本统计",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Counts characters, words and sentences, with words per item by "
            "element kind and words per page on documents."
        ),
        es=(
            "Cuenta caracteres, palabras y oraciones, con palabras por elemento "
            "según su tipo y palabras por página en documentos."
        ),
        pt=(
            "Conta caracteres, palavras e frases, com palavras por item por tipo "
            "de elemento e palavras por página em documentos."
        ),
        de=(
            "Zählt Zeichen, Wörter und Sätze, mit Wörtern pro Element nach "
            "Elementart und Wörtern pro Seite bei Dokumenten."
        ),
        zh=(
            "统计字符、单词和句子数量；在文档中按元素类型显示每个元素的词数，并按页统计"
            "词数。"
        ),
    )
    metadata: Dict[str, Any] = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 1},
        "data_kinds": [DATASET, DOCUMENT],
    }

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Build the statistics figure.

        Parameters
        ----------
        dataset : DashAIDataset
            The selected text, with ``kind`` and ``page`` on a document.
        explorer_info : Explorer
            The explorer record.

        Returns
        -------
        plotly.graph_objects.Figure
            A table of totals above one or two charts.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        values = self.text_column(dataset, explorer_info)
        counts = [text_counts(value) for value in values]
        words = [count["words"] for count in counts]
        table = dataset.arrow_table
        kinds = (
            table.column("kind").to_pylist() if "kind" in table.column_names else None
        )
        pages = (
            table.column("page").to_pylist() if "page" in table.column_names else None
        )
        has_pages = pages is not None and any(page is not None for page in pages)

        rows = self.summary_rows(counts)
        titles = ["Summary"]
        if kinds is not None:
            titles.append("Words per item by kind")
        else:
            titles.append("Words per value")
        if has_pages:
            titles.append("Words per page")
        figure = make_subplots(
            rows=len(titles),
            cols=1,
            specs=[[{"type": "table"}]] + [[{}]] * (len(titles) - 1),
            subplot_titles=titles,
            vertical_spacing=0.08,
        )
        figure.add_trace(
            go.Table(
                header={"values": ["Measure", "Value"]},
                cells={"values": [[row[0] for row in rows], [row[1] for row in rows]]},
            ),
            row=1,
            col=1,
        )
        if kinds is not None:
            for kind in dict.fromkeys(kinds):
                figure.add_trace(
                    go.Box(
                        y=[w for w, k in zip(words, kinds, strict=True) if k == kind],
                        name=kind,
                        boxpoints="outliers",
                    ),
                    row=2,
                    col=1,
                )
        else:
            figure.add_trace(go.Histogram(x=words, name="words"), row=2, col=1)
        if has_pages:
            per_page: Dict[int, int] = {}
            for page, count in zip(pages, words, strict=True):
                if page is not None:
                    per_page[page] = per_page.get(page, 0) + count
            figure.add_trace(
                go.Bar(x=list(per_page), y=list(per_page.values()), name="pages"),
                row=3,
                col=1,
            )
            figure.update_xaxes(title_text="Page", row=3, col=1)
        figure.update_layout(
            title=explorer_info.name or "Text statistics",
            height=360 * len(titles),
            showlegend=False,
        )
        return figure

    @staticmethod
    def summary_rows(counts: List[Dict[str, int]]) -> List[List[Any]]:
        """Return the measures shown in the summary table.

        Parameters
        ----------
        counts : List[Dict[str, int]]
            The counts of each item from :func:`text_counts`.

        Returns
        -------
        List[List[Any]]
            ``[measure, value]`` rows.
        """
        words = [count["words"] for count in counts]
        return [
            ["Items", len(counts)],
            ["Empty items", sum(1 for count in counts if count["characters"] == 0)],
            ["Characters", sum(count["characters"] for count in counts)],
            ["Words", sum(words)],
            ["Sentences", sum(count["sentences"] for count in counts)],
            ["Mean words per item", round(statistics.fmean(words), 1) if words else 0],
            ["Median words per item", statistics.median(words) if words else 0],
            ["Most words in an item", max(words, default=0)],
        ]
