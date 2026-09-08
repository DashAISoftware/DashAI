"""Tests for the per family model artifact mixins."""

import numpy as np
import pandas as pd
import pytest

from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.models.model_artifact_context import ModelArtifactContext
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.k_neighbors_regression import KNeighborsRegression
from DashAI.back.models.scikit_learn.mlp_classifier import MLPClassifier
from DashAI.back.models.scikit_learn.model_artifact_mixins import MAX_PLOTTED_TREES
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)


@pytest.fixture
def context():
    return ModelArtifactContext(feature_names=["a", "b"], class_names=["no", "yes"])


@pytest.fixture
def training_frame():
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"a": rng.normal(0, 3, 80), "b": rng.normal(0, 1, 80)})
    return x, (x["a"] > 0).astype(int).to_numpy()


@pytest.fixture
def fitted(training_frame):
    x, y = training_frame

    def _fitted(model_class, **params):
        model = model_class(**params)
        model.fit(x, y)
        return model

    return _fitted


def _types(artifacts):
    return [getattr(item, "type", None) for item in artifacts]


def test_unfitted_model_returns_no_artifacts(context):
    assert DecisionTreeClassifier(max_depth=3).get_model_artifacts(context) == []


def test_decision_tree_returns_tree_and_importances(context, fitted):
    artifacts = fitted(DecisionTreeClassifier, max_depth=3).get_model_artifacts(context)

    assert _types(artifacts) == ["plotly", "plotly"]
    assert normalize_artifacts(artifacts)[0]["index"] == 0


def test_forest_groups_its_trees_and_states_the_truncation(context, fitted):
    artifacts = fitted(
        RandomForestClassifier, n_estimators=30, max_depth=2
    ).get_model_artifacts(context)

    grouped = [item for item in artifacts if getattr(item, "type", None) == "grouped"]
    assert len(grouped) == 1
    assert len(grouped[0].groups) == MAX_PLOTTED_TREES
    assert "text" in _types(artifacts)


def test_small_forest_is_not_truncated(context, fitted):
    artifacts = fitted(
        RandomForestClassifier, n_estimators=3, max_depth=2
    ).get_model_artifacts(context)

    grouped = [item for item in artifacts if getattr(item, "type", None) == "grouped"]
    assert len(grouped[0].groups) == 3
    assert "text" not in _types(artifacts)


def test_mlp_returns_only_its_weights(context, fitted):
    """The training loss curve belongs to the metrics system, not here.

    It is one scalar per epoch, which ``Metric`` already models at STEP level,
    so the visualization must not carry a second copy of it.
    """
    artifacts = fitted(
        MLPClassifier, hidden_layer_size=4, max_iter=20
    ).get_model_artifacts(context)

    assert _types(artifacts) == ["grouped"]
    assert len(artifacts[0].groups) == 2


def test_every_mixin_output_normalizes(context, fitted):
    models = (
        fitted(DecisionTreeClassifier, max_depth=3),
        fitted(RandomForestClassifier, n_estimators=5, max_depth=2),
        fitted(MLPClassifier, hidden_layer_size=4, max_iter=20),
    )
    for model in models:
        items = normalize_artifacts(model.get_model_artifacts(context))
        assert items
        for item in items:
            assert item["type"] in {"plotly", "table", "text", "image", "grouped"}


def test_wired_models_report_support():
    for model_class in (
        DecisionTreeClassifier,
        RandomForestClassifier,
        MLPClassifier,
    ):
        assert model_class.supports_model_artifacts() is True


def test_nearest_neighbours_has_no_model_visualization():
    """A decision surface is a behavioral probe, so it is a global explainer.

    Nothing in a fitted k-neighbours model is renderable without sweeping a
    feature range through ``predict``, so these models declare no support at
    all rather than borrowing the explainer's job.
    """
    assert KNeighborsClassifier.supports_model_artifacts() is False
    assert KNeighborsRegression.supports_model_artifacts() is False
