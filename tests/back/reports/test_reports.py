"""Unit tests for the concrete evaluation reports."""

import json

import numpy as np
import pytest

from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.reports.base_report import (
    BaseReport,
    ReportError,
    as_labels,
    resolve_class_names,
)
from DashAI.back.reports.classification.confusion_matrix import ConfusionMatrix
from DashAI.back.reports.classification.per_class_breakdown import (
    PerClassBreakdown,
)
from DashAI.back.reports.classification.precision_recall_curve import (
    PrecisionRecallCurve,
)
from DashAI.back.reports.classification.roc_curve import RocCurve
from DashAI.back.reports.regression.predicted_vs_actual import PredictedVsActual
from DashAI.back.reports.regression.residual_histogram import ResidualHistogram
from DashAI.back.reports.regression.residual_plot import ResidualPlot

CLASS_NAMES = ["setosa", "versicolor", "virginica"]


@pytest.fixture
def classification_data():
    """Three classes, probabilities that mostly agree with the truth."""
    rng = np.random.default_rng(0)
    y_true = np.array([0, 0, 1, 1, 2, 2, 0, 1, 2, 1])
    probabilities = rng.random((len(y_true), 3))
    # Bias each row toward its true class so the curves are non degenerate.
    probabilities[np.arange(len(y_true)), y_true] += 2.0
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    return y_true, probabilities


@pytest.fixture
def regression_data():
    rng = np.random.default_rng(0)
    y_true = rng.normal(10, 3, 50)
    return y_true, y_true + rng.normal(0, 1, 50)


def _figure(artifact):
    assert artifact.type == "plotly"
    return json.loads(artifact.payload)


def test_as_labels_argmaxes_a_probability_matrix():
    assert as_labels(np.array([[0.1, 0.9], [0.8, 0.2]])).tolist() == [1, 0]
    assert as_labels(np.array([1, 0])).tolist() == [1, 0]


def test_resolve_class_names_fills_gaps():
    assert resolve_class_names(["a"], 3) == ["a", "1", "2"]
    assert resolve_class_names(None, 2) == ["0", "1"]


def test_confusion_matrix_counts_every_pair(classification_data):
    y_true, probabilities = classification_data

    artifacts = ConfusionMatrix().compute(y_true, probabilities, CLASS_NAMES)
    figure = _figure(artifacts[0])

    assert figure["data"][0]["type"] == "heatmap"
    assert list(figure["data"][0]["x"]) == CLASS_NAMES
    # Raw counts must add up to the number of samples.
    total = sum(sum(row) for row in figure["data"][0]["z"])
    assert total == len(y_true)


def test_confusion_matrix_row_normalizes(classification_data):
    y_true, probabilities = classification_data

    figure = _figure(
        ConfusionMatrix(normalize="true").compute(y_true, probabilities, CLASS_NAMES)[0]
    )

    for row in figure["data"][0]["z"]:
        assert sum(row) == pytest.approx(1.0)


def test_roc_curve_has_a_trace_per_class_plus_chance(classification_data):
    y_true, probabilities = classification_data

    figure = _figure(RocCurve().compute(y_true, probabilities, CLASS_NAMES)[0])

    assert len(figure["data"]) == len(CLASS_NAMES) + 1
    assert "AUC" in figure["data"][1]["name"]


def test_roc_curve_draws_one_curve_for_a_binary_problem():
    y_true = np.array([0, 1, 0, 1])
    probabilities = np.array([[0.8, 0.2], [0.3, 0.7], [0.6, 0.4], [0.2, 0.8]])

    figure = _figure(RocCurve().compute(y_true, probabilities, ["no", "yes"])[0])

    # Chance line plus a single curve, not two mirrored ones.
    assert len(figure["data"]) == 2


def test_roc_curve_refuses_hard_labels():
    with pytest.raises(ReportError, match="class probabilities"):
        RocCurve().compute(np.array([0, 1]), np.array([0, 1]), ["no", "yes"])


def test_roc_curve_refuses_a_single_class_split():
    probabilities = np.array([[0.9, 0.1], [0.8, 0.2]])
    with pytest.raises(ReportError, match="single class"):
        RocCurve().compute(np.array([0, 0]), probabilities, ["no", "yes"])


def test_precision_recall_curve_annotates_average_precision(classification_data):
    y_true, probabilities = classification_data

    figure = _figure(
        PrecisionRecallCurve().compute(y_true, probabilities, CLASS_NAMES)[0]
    )

    assert len(figure["data"]) == len(CLASS_NAMES)
    assert "AP" in figure["data"][0]["name"]


def test_per_class_breakdown_has_a_row_per_class_and_averages(classification_data):
    y_true, probabilities = classification_data

    artifacts = PerClassBreakdown().compute(y_true, probabilities, CLASS_NAMES)

    assert artifacts[0].type == "table"
    payload = artifacts[0].payload
    assert payload.columns == ["Class", "Precision", "Recall", "F1", "Support"]
    assert len(payload.rows) == len(CLASS_NAMES) + 2
    assert payload.rows[-2][0] == "macro avg"
    assert payload.rows[-1][0] == "weighted avg"


def test_predicted_vs_actual_draws_the_identity_line(regression_data):
    y_true, y_pred = regression_data

    figure = _figure(PredictedVsActual().compute(y_true, y_pred)[0])

    modes = [trace.get("mode") for trace in figure["data"]]
    assert "lines" in modes
    assert "markers" in modes


def test_residual_plot_centers_on_zero(regression_data):
    y_true, y_pred = regression_data

    figure = _figure(ResidualPlot().compute(y_true, y_pred)[0])

    residual_trace = figure["data"][1]
    assert np.mean(residual_trace["y"]) == pytest.approx(
        np.mean(y_true - y_pred), abs=1e-9
    )


def test_residual_histogram_honours_its_bin_count(regression_data):
    y_true, y_pred = regression_data

    figure = _figure(ResidualHistogram(bins=12).compute(y_true, y_pred)[0])

    assert figure["data"][0]["type"] == "histogram"
    assert figure["data"][0]["nbinsx"] == 12


def test_every_report_output_normalizes(classification_data, regression_data):
    y_true, probabilities = classification_data
    reg_true, reg_pred = regression_data

    outputs = [
        ConfusionMatrix().compute(y_true, probabilities, CLASS_NAMES),
        RocCurve().compute(y_true, probabilities, CLASS_NAMES),
        PrecisionRecallCurve().compute(y_true, probabilities, CLASS_NAMES),
        PerClassBreakdown().compute(y_true, probabilities, CLASS_NAMES),
        PredictedVsActual().compute(reg_true, reg_pred),
        ResidualPlot().compute(reg_true, reg_pred),
        ResidualHistogram().compute(reg_true, reg_pred),
    ]
    for output in outputs:
        for item in normalize_artifacts(output):
            assert item["type"] in {"plotly", "table", "text", "image", "grouped"}


def test_reports_declare_their_probability_requirement():
    assert RocCurve.REQUIRES_PROBABILITIES is True
    assert PrecisionRecallCurve.REQUIRES_PROBABILITIES is True
    assert ConfusionMatrix.REQUIRES_PROBABILITIES is False
    assert ResidualPlot.REQUIRES_PROBABILITIES is False
    assert RocCurve.get_metadata()["requires_probabilities"] is True


def test_reports_are_registered_under_one_type():
    """The registry keys every report under the same component type."""
    for report in (
        ConfusionMatrix,
        RocCurve,
        PrecisionRecallCurve,
        PerClassBreakdown,
        PredictedVsActual,
        ResidualPlot,
        ResidualHistogram,
    ):
        assert report.TYPE == "Report"
        assert issubclass(report, BaseReport)
        assert report.COMPATIBLE_COMPONENTS


def test_a_report_never_receives_model_inputs():
    """Reports compare predictions against the truth and nothing else.

    Taking X would make it an explainer, so the contract must not offer one.
    """
    import inspect

    parameters = inspect.signature(BaseReport.compute).parameters
    assert list(parameters) == ["self", "y_true", "y_pred", "class_names"]
