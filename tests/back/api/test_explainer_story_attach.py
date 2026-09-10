"""Unit tests for the story-attaching helpers in explainers endpoints.

``explainer_job.py`` always runs ``plot()``'s output through
``normalize_artifacts`` *before* pickling it, so ``plot_path``/``plots_path``
on disk hold plain wire-format dicts, never the live ``Artifact``/
``ArtifactGroup`` instances ``plot()`` returned. These tests exercise
``_attach_stories`` against that real, dict-shaped input (not hand-built
Pydantic objects) to guard against the regression where dict-shaped groups
crashed the plot endpoint with a 500 instead of just omitting the story.

Only the pure helper functions are imported, not the FastAPI app, so this
runs without booting a TestClient.
"""

from unittest.mock import MagicMock

from DashAI.back.api.api_v1.endpoints.explainers import (
    _as_artifact_target,
    _as_group_target,
    _attach_stories,
)
from DashAI.back.core.artifacts import Artifact, ArtifactGroup, normalize_artifacts
from DashAI.back.explainability.explainers.kernel_shap import KernelShap
from DashAI.back.explainability.explainers.permutation_feature_importance import (
    PermutationFeatureImportance,
)


def test_attach_stories_global_dict_shaped_matches_job_output():
    """Global plot: raw items are dicts, as ``explainer_job.py`` pickles them."""
    explanation = {
        "features": ["age", "income"],
        "importances_mean": [0.084, 0.061],
        "importances_std": [0.01, 0.01],
    }
    explainer = PermutationFeatureImportance(model=MagicMock(), scoring="accuracy")

    # Mirrors explainer_job.py: normalize_artifacts(explainer.plot(explanation)).
    raw = normalize_artifacts(explainer.plot(explanation))
    normalized = normalize_artifacts(explainer.plot(explanation))

    _attach_stories(normalized, raw, explanation, explainer)

    group = normalized[0]["groups"][0]
    assert group["title"] == "Top 2 features"
    assert group["story"]["en"].startswith("Ranked by the drop in accuracy")


def test_attach_stories_local_dict_shaped_matches_job_output():
    """Local plot: raw items are dicts, as ``explainer_job.py`` pickles them."""
    explanation = {
        "metadata": {"feature_names": ["age", "income"], "target_names": ["no", "yes"]},
        "base_values": [0.4, 0.6],
        0: {
            "instance_values": [35, 50000],
            "model_prediction": [0.2, 0.8],
            "shap_values": [[-0.1, -0.05], [0.1, 0.05]],
        },
    }
    explainer = KernelShap(model=MagicMock())

    # Mirrors explainer_job.py:
    # normalize_artifacts(explainer.plot(explanation), create_grouped=True).
    raw = normalize_artifacts(explainer.plot(explanation), create_grouped=True)
    normalized = normalize_artifacts(explainer.plot(explanation), create_grouped=True)

    _attach_stories(normalized, raw, explanation, explainer, create_grouped=True)

    group = normalized[0]["groups"][0]
    assert group["title"] == "Instance 1"
    assert "yes" in group["story"]["en"]


def test_attach_stories_global_legacy_bare_string_raw_does_not_crash():
    """Explanations persisted before explainer_job.py normalized prior to
    pickling (58c6262dc, 2026-07-10) still have `raw` on disk as a bare
    plotly-JSON string, not wrapped in a list. Regression test for the 500
    this used to cause (`ValueError: zip() argument 2 is shorter than
    argument 1`, since zip() iterates the string's characters): it must
    degrade to no story instead.
    """
    explanation = {
        "features": ["age", "income"],
        "importances_mean": [0.084, 0.061],
        "importances_std": [0.01, 0.01],
    }
    explainer = PermutationFeatureImportance(model=MagicMock(), scoring="accuracy")
    normalized = normalize_artifacts(explainer.plot(explanation))

    legacy_raw = '{"data": [], "layout": {}}'

    _attach_stories(normalized, legacy_raw, explanation, explainer)

    assert normalized[0].get("story") is None


def test_attach_stories_local_legacy_bare_dict_raw_does_not_crash():
    """Local explanations persisted before 58c6262dc still have `raw` on
    disk as a bare dict (plot()'s return value itself), not wrapped in a
    list. Regression test for the 500 this used to cause (`KeyError: 0` from
    `_is_grouped_raw(raw[0])` indexing a dict): it must degrade to no story
    instead.
    """
    explanation = {
        "metadata": {"feature_names": ["age", "income"], "target_names": ["no", "yes"]},
        "base_values": [0.4, 0.6],
        0: {
            "instance_values": [35, 50000],
            "model_prediction": [0.2, 0.8],
            "shap_values": [[-0.1, -0.05], [0.1, 0.05]],
        },
    }
    explainer = KernelShap(model=MagicMock())
    normalized = normalize_artifacts(explainer.plot(explanation), create_grouped=True)

    legacy_raw = {"title": "legacy plot"}

    _attach_stories(normalized, legacy_raw, explanation, explainer, create_grouped=True)

    assert normalized[0]["groups"][0].get("story") is None


def test_attach_stories_is_a_noop_without_a_story_explainer():
    """No explainer (couldn't be built) means no story, not a crash."""
    explanation = {
        "features": ["age"],
        "importances_mean": [0.1],
        "importances_std": [0.0],
    }
    explainer = PermutationFeatureImportance(model=MagicMock(), scoring="accuracy")
    raw = normalize_artifacts(explainer.plot(explanation))
    normalized = normalize_artifacts(explainer.plot(explanation))

    _attach_stories(normalized, raw, explanation, None)

    assert normalized[0]["groups"][0].get("story") is None


def test_as_group_target_builds_a_real_artifact_group_from_a_dict():
    """A dict coerces into a real ``ArtifactGroup`` (isinstance must hold)."""
    group = _as_group_target({"title": "Top 2 features", "artifacts": []})
    assert isinstance(group, ArtifactGroup)
    assert group.title == "Top 2 features"

    live = ArtifactGroup(title="already live", artifacts=[])
    assert _as_group_target(live) is live


def test_as_artifact_target_builds_a_real_artifact_from_a_dict():
    """A dict coerces into a real ``Artifact`` (isinstance must hold)."""
    artifact = _as_artifact_target({"title": "Permutation Feature Importance"})
    assert isinstance(artifact, Artifact)
    assert not isinstance(artifact, ArtifactGroup)
    assert artifact.title == "Permutation Feature Importance"
