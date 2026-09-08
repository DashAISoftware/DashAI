"""Per segment reference against translation comparison table."""

from typing import List, Optional

import numpy as np

from DashAI.back.core.artifacts import (
    Artifact,
    TableArtifact,
    TableCell,
    TablePayload,
)
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import BaseReport, ReportError


def as_text_pairs(y_true, y_pred):
    """Flatten the truth and predictions into aligned lists of strings.

    Parameters
    ----------
    y_true : array_like
        Reference translations, one per row.
    y_pred : array_like
        The model's translations for the same rows.

    Returns
    -------
    tuple of list of str
        The references and the hypotheses, both as flat string lists.

    Raises
    ------
    ReportError
        If the two inputs hold a different number of segments.
    """
    truth = [str(value) for value in np.asarray(y_true).ravel()]
    hypothesis = [str(value) for value in np.asarray(y_pred).ravel()]
    if len(truth) != len(hypothesis):
        raise ReportError(
            "The number of reference and translated segments must match, "
            f"given {len(truth)} and {len(hypothesis)}."
        )
    return truth, hypothesis


def per_segment_scores(y_true, y_pred) -> List[float]:
    """Score every segment with sentence level BLEU.

    Sentence BLEU on short strings is degenerate without smoothing, so the
    score uses exponential smoothing and the effective order, which makes an
    exact match a 100 and a complete miss a 0. It is a diagnostic, not the
    corpus level BLEU the metric reports, so the two are free to disagree on
    any one split.

    Parameters
    ----------
    y_true : array_like
        Reference translations, one per row.
    y_pred : array_like
        The model's translations for the same rows.

    Returns
    -------
    list of float
        One score in the 0-100 range per segment.
    """
    from sacrebleu.metrics import BLEU

    truth, hypothesis = as_text_pairs(y_true, y_pred)
    bleu = BLEU(smooth_method="exp", effective_order=True)
    scores = [
        float(bleu.sentence_score(hypothesis[index], [truth[index]]).score)
        for index in range(len(truth))
    ]
    return [min(100.0, max(0.0, score)) for score in scores]


class PerSegmentComparisonSchema(BaseSchema):
    """Schema that configures the per segment comparison report."""

    highlight_count: schema_field(
        int_field(ge=0, le=100),
        placeholder=5,
        description=MultilingualString(
            en="How many of the lowest scoring segments to highlight.",
            es="Cuántos de los segmentos con menor puntuación resaltar.",
            pt="Quantos dos segmentos com menor pontuação destacar.",
            de="Wie viele der am schlechtesten bewerteten Segmente hervorheben.",
            zh="要突出显示的最低评分片段数量。",
        ),
        alias=MultilingualString(
            en="Highlight count",
            es="Cantidad a resaltar",
            pt="Quantidade a destacar",
            de="Hervorzuhebende Anzahl",
            zh="突出显示数量",
        ),
    )  # type: ignore


class PerSegmentComparison(BaseReport):
    """Reference against translation for every segment, worst ones highlighted.

    The corpus level BLEU, CHRF and TER metrics condense a whole split into
    one number. This table is the split itself: it pairs each reference with
    its translation and a sentence level score, and highlights the lowest
    scoring rows so the segments dragging the aggregate down are the first
    thing seen. A concentration of low scores in long or short segments, or
    around a particular topic, is exactly what the average cannot say.
    """

    SCHEMA = PerSegmentComparisonSchema
    COMPATIBLE_COMPONENTS = ["TranslationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Per Segment Comparison",
        es="Comparación por Segmento",
        pt="Comparação por Segmento",
        de="Vergleich je Segment",
        zh="按片段比较",
    )
    DESCRIPTION: str = MultilingualString(
        en="Reference against translation per segment, with the worst highlighted.",
        es=("Referencia contra traducción por segmento, con los peores resaltados."),
        pt=("Referência contra tradução por segmento, com os piores destacados."),
        de=(
            "Referenz gegen Übersetzung je Segment, mit hervorgehobenen Schlechtesten."
        ),
        zh="逐个片段对比参考译文与翻译结果，并突出显示最差片段。",
    )
    COLOR: str = "#66BB6A"
    ICON: str = "TableChart"

    def __init__(self, highlight_count: int = 5, **kwargs) -> None:
        """Initialise the report.

        Parameters
        ----------
        highlight_count : int
            How many of the lowest scoring segments to highlight.
        **kwargs : dict
            Ignored; accepted so unknown stored parameters do not break loading.
        """
        self.highlight_count = highlight_count

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the per segment comparison table.

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
            A single table, one row per segment plus the average row.
        """
        truth, hypothesis = as_text_pairs(y_true, y_pred)
        scores = per_segment_scores(y_true, y_pred)

        rows = [
            [
                index + 1,
                truth[index],
                hypothesis[index],
                round(scores[index], 2),
            ]
            for index in range(len(truth))
        ]
        average = sum(scores) / len(scores) if scores else 0.0
        rows.append(["average", "", "", round(float(average), 2)])

        count = min(int(self.highlight_count), len(scores))
        worst = sorted(range(len(scores)), key=lambda i: scores[i])[:count]
        highlight = [TableCell(row=index, column=3) for index in worst]

        return [
            TableArtifact(
                payload=TablePayload(
                    columns=["#", "Reference", "Translation", "Score"],
                    rows=rows,
                    highlight=highlight,
                ),
                title="Per segment comparison",
            )
        ]
