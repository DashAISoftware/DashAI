from typing import Dict, List

import numpy as np
import pytest
from datasets import Dataset

from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.metrics.classification.f1 import F1
from DashAI.back.metrics.classification.precision import Precision
from DashAI.back.metrics.classification.recall import Recall


@pytest.fixture(scope="module", name="metric_input")
def fixture_metric_input() -> dict:
    return {
        "true_labels": Dataset.from_list([{"foo": 1}, {"foo": 2}, {"foo": 0}]),
        "pred_labels": np.array([[0.1, 0.1, 0.8], [0.0, 0.8, 0.2], [0.9, 0.0, 0.5]]),
        "wrong_size_labels": np.array([[0.1, 0.1, 0.8], [0.9, 0.0, 0.5]]),
    }


def test_accuracy(metric_input: Dict[str, List[int]]):
    score = Accuracy.score(metric_input["true_labels"], metric_input["pred_labels"])

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_precision(metric_input: Dict[str, List[int]]):
    score = Precision.score(metric_input["true_labels"], metric_input["pred_labels"])

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_recall(metric_input: Dict[str, List[int]]):
    score = Recall.score(metric_input["true_labels"], metric_input["pred_labels"])

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_f1_score(metric_input: Dict[str, List[int]]):
    score = F1.score(metric_input["true_labels"], metric_input["pred_labels"])

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_metrics_different_input_sizes(metric_input: Dict[str, List[int]]):
    error_pattern = (
        r"The length of the true labels and the predicted labels must be equal, "
        r"given: len\(true_labels\) = 3 and len\(pred_labels\) = 2\."
    )

    with pytest.raises(
        ValueError,
        match=error_pattern,
    ):
        Accuracy.score(metric_input["true_labels"], metric_input["wrong_size_labels"])

    with pytest.raises(
        ValueError,
        match=error_pattern,
    ):
        Precision.score(metric_input["true_labels"], metric_input["wrong_size_labels"])

    with pytest.raises(
        ValueError,
        match=error_pattern,
    ):
        Recall.score(metric_input["true_labels"], metric_input["wrong_size_labels"])

    with pytest.raises(
        ValueError,
        match=error_pattern,
    ):
        F1.score(metric_input["true_labels"], metric_input["wrong_size_labels"])
