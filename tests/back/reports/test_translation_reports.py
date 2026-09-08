"""Unit tests for the translation evaluation reports."""

import json

import numpy as np
import pytest

from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.translation.length_comparison import LengthComparison
from DashAI.back.reports.translation.per_segment_comparison import (
    PerSegmentComparison,
)
from DashAI.back.reports.translation.segment_score_distribution import (
    SegmentScoreDistribution,
)

REFERENCE = [
    "the cat sat on the mat",
    "good morning everyone",
    "the quick brown fox jumps over the lazy dog",
    "please close the window",
    "i would like a cup of coffee",
]
HYPOTHESIS = [
    "the cat sat on the mat",
    "good morning everyone",
    "the quick brown fox jumps over the lazy dog",
    "please open the window",
    "i would like a cup of tea",
]


@pytest.fixture
def translation_data():
    """Two exact matches, two imperfect ones and one nearly unrelated."""
    return np.array(REFERENCE), np.array(HYPOTHESIS)


def _figure(artifact):
    assert artifact.type == "plotly"
    return json.loads(artifact.payload)


def test_per_segment_comparison_has_a_row_per_segment_plus_average(
    translation_data,
):
    y_true, y_pred = translation_data

    artifacts = PerSegmentComparison(highlight_count=2).compute(y_true, y_pred)

    assert artifacts[0].type == "table"
    payload = artifacts[0].payload
    assert payload.columns == ["#", "Reference", "Translation", "Score"]
    assert len(payload.rows) == len(y_true) + 1
    assert payload.rows[-1][0] == "average"


def test_per_segment_comparison_scores_an_exact_match_100(translation_data):
    y_true, y_pred = translation_data

    artifacts = PerSegmentComparison().compute(y_true, y_pred)
    rows = artifacts[0].payload.rows

    exact = [row for row in rows[: len(y_true)] if row[1] == row[2]]
    assert exact
    for row in exact:
        assert row[3] == pytest.approx(100.0, abs=1e-6)


def test_per_segment_comparison_highlights_the_worst_segments(translation_data):
    y_true, y_pred = translation_data

    artifacts = PerSegmentComparison(highlight_count=2).compute(y_true, y_pred)
    payload = artifacts[0].payload

    highlighted_rows = [cell.row for cell in payload.highlight]
    assert len(highlighted_rows) == 2
    assert all(cell.column == 3 for cell in payload.highlight)

    segment_rows = payload.rows[: len(y_true)]
    worst = sorted(range(len(segment_rows)), key=lambda i: segment_rows[i][3])[:2]
    assert sorted(highlighted_rows) == sorted(worst)


def test_segment_score_distribution_is_a_histogram(translation_data):
    y_true, y_pred = translation_data

    figure = _figure(SegmentScoreDistribution(bins=8).compute(y_true, y_pred)[0])

    assert figure["data"][0]["type"] == "histogram"
    assert figure["data"][0]["nbinsx"] == 8
    # Scores sit on the 0-100 scale.
    assert min(figure["data"][0]["x"]) >= 0
    assert max(figure["data"][0]["x"]) <= 100


def test_length_comparison_has_identity_line_and_points(translation_data):
    y_true, y_pred = translation_data

    figure = _figure(LengthComparison().compute(y_true, y_pred)[0])

    modes = [trace.get("mode") for trace in figure["data"]]
    assert "lines" in modes
    assert "markers" in modes
    assert list(figure["data"][1]["x"]) == [len(str(sample)) for sample in y_true]
    assert list(figure["data"][1]["y"]) == [len(str(sample)) for sample in y_pred]


def test_every_translation_report_output_normalizes(translation_data):
    y_true, y_pred = translation_data

    outputs = [
        PerSegmentComparison().compute(y_true, y_pred),
        SegmentScoreDistribution().compute(y_true, y_pred),
        LengthComparison().compute(y_true, y_pred),
    ]
    for output in outputs:
        for item in normalize_artifacts(output):
            assert item["type"] in {"plotly", "table", "text", "image", "grouped"}


def test_translation_reports_are_registered_for_the_task():
    for report in (
        PerSegmentComparison,
        SegmentScoreDistribution,
        LengthComparison,
    ):
        assert report.TYPE == "Report"
        assert issubclass(report, BaseReport)
        assert report.COMPATIBLE_COMPONENTS == ["TranslationTask"]
