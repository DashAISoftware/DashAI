"""Unit tests for the shared ``apply_plot_overrides`` helper.

These tests import only the pure helper function, not the FastAPI app, so
they can run without the heavy explainer dependencies (grad_cam, dice_ml,
lime) that are currently missing from the project venv and would otherwise
be pulled in by component registration when booting a TestClient.

NOTE: The HTTP round-trip tests for the override endpoints (PUT/DELETE
``/{scope}/plot/{explainer_id}/override``) described in the task brief are
deferred until the environment has the explainer dependencies installed, so
a TestClient can be instantiated without import errors.
"""

import json

from DashAI.back.core.artifacts import apply_plot_overrides


def test_apply_overrides_replaces_plotly_payload():
    """An override at a plotly artifact's index replaces its payload."""
    artifacts = [
        {"type": "plotly", "payload": "original", "title": "Plot 0", "index": 0},
    ]
    figure = {"data": [], "layout": {"title": "edited"}}

    result = apply_plot_overrides(artifacts, {"0": figure})

    assert result[0]["payload"] != "original"
    assert json.loads(result[0]["payload"]) == figure


def test_apply_overrides_leaves_non_plotly_artifact_unchanged():
    """An override targeting a non-plotly artifact index is ignored."""
    artifacts = [
        {"type": "image", "payload": "original-image", "title": "Image 0", "index": 0},
    ]

    result = apply_plot_overrides(artifacts, {"0": {"data": [], "layout": {}}})

    assert result[0]["payload"] == "original-image"


def test_apply_overrides_ignores_out_of_range_index():
    """An override with an out-of-range index does not raise or mutate."""
    artifacts = [
        {"type": "plotly", "payload": "original", "title": "Plot 0", "index": 0},
    ]

    result = apply_plot_overrides(artifacts, {"5": {"data": []}})

    assert result[0]["payload"] == "original"


def test_apply_overrides_returns_unchanged_for_none_or_empty():
    """None or empty overrides leave the artifacts list unchanged."""
    artifacts = [
        {"type": "plotly", "payload": "original", "title": "Plot 0"},
    ]

    assert apply_plot_overrides(artifacts, None) == artifacts
    assert apply_plot_overrides(artifacts, {}) == artifacts


def test_apply_overrides_replaces_leaf_nested_in_group():
    """An override reaches a plotly leaf nested inside a grouped artifact."""
    artifacts = [
        {
            "type": "grouped",
            "title": "Instances",
            "groups": [
                {
                    "title": "Instance 0",
                    "artifacts": [
                        {
                            "type": "plotly",
                            "payload": "original",
                            "title": "Plot",
                            "index": 0,
                        },
                    ],
                },
            ],
        },
    ]
    figure = {"data": [], "layout": {"title": "edited"}}

    result = apply_plot_overrides(artifacts, {"0": figure})
    leaf = result[0]["groups"][0]["artifacts"][0]

    assert json.loads(leaf["payload"]) == figure
    assert leaf["overridden"] is True
