import base64
import json

import pytest

from DashAI.back.core.artifacts import (
    Artifact,
    ImageArtifact,
    ImagePayload,
    PlotlyArtifact,
    TableArtifact,
    TableCell,
    TablePayload,
    TextArtifact,
    normalize_artifacts,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def test_plotly_artifact_to_dict():
    artifact = PlotlyArtifact(payload='{"data": []}', title="A plot")
    assert artifact.to_dict() == {
        "type": "plotly",
        "payload": '{"data": []}',
        "title": "A plot",
        "role": "explanation",
    }


def test_plotly_artifact_accepts_figure():
    import plotly.graph_objects as go

    figure = go.Figure(data=[go.Bar(x=["a"], y=[1])])
    artifact = PlotlyArtifact(payload=figure)
    parsed = json.loads(artifact.payload)
    assert parsed["data"][0]["type"] == "bar"


def test_table_artifact_to_dict():
    artifact = TableArtifact(
        payload=TablePayload(
            columns=["a", "b"],
            rows=[[1, 2], [3, 4]],
            highlight=[TableCell(row=1, column=0)],
        ),
        title="A table",
    )
    assert artifact.to_dict() == {
        "type": "table",
        "payload": {
            "columns": ["a", "b"],
            "rows": [[1, 2], [3, 4]],
            "highlight": [{"row": 1, "column": 0}],
        },
        "title": "A table",
        "role": "explanation",
    }


def test_table_artifact_rejects_ragged_rows():
    with pytest.raises(ValueError, match="expected 2"):
        TablePayload(columns=["a", "b"], rows=[[1, 2], [3]])


def test_table_artifact_rejects_out_of_bounds_highlight():
    with pytest.raises(ValueError, match="out of bounds"):
        TablePayload(
            columns=["a"],
            rows=[[1]],
            highlight=[TableCell(row=1, column=0)],
        )


def test_text_artifact_to_dict():
    artifact = TextArtifact(payload="line 1\nline 2")
    assert artifact.to_dict() == {
        "type": "text",
        "payload": "line 1\nline 2",
        "title": None,
        "role": "explanation",
    }


def test_image_artifact_encodes_bytes():
    artifact = ImageArtifact(payload=ImagePayload(data=PNG_BYTES))
    decoded = base64.b64decode(artifact.payload.data)
    assert decoded == PNG_BYTES


def test_image_artifact_rejects_invalid_base64():
    with pytest.raises(ValueError, match="base64"):
        ImagePayload(data="not base64!!")


def test_image_artifact_from_dashai_image():
    from DashAI.back.types.dashai_image import DashAIImage

    image = DashAIImage(bytes=PNG_BYTES, path="img.png")
    artifact = ImageArtifact.from_dashai_image(image, title="An image")
    assert artifact.payload.mime == "image/png"
    assert base64.b64decode(artifact.payload.data) == PNG_BYTES
    assert artifact.title == "An image"


def test_image_artifact_from_dashai_image_without_bytes():
    from DashAI.back.types.dashai_image import DashAIImage

    with pytest.raises(ValueError, match="no bytes"):
        ImageArtifact.from_dashai_image(DashAIImage())


@pytest.mark.parametrize(
    "artifact",
    [
        PlotlyArtifact(payload='{"data": []}', title="p"),
        TableArtifact(payload=TablePayload(columns=["a"], rows=[[1]])),
        TextArtifact(payload="hello"),
        ImageArtifact(payload=ImagePayload(data=PNG_BYTES)),
    ],
)
def test_from_dict_round_trip(artifact):
    restored = Artifact.from_dict(artifact.to_dict())
    assert type(restored) is type(artifact)
    assert restored == artifact


def test_from_dict_rejects_unknown_type():
    with pytest.raises(ValueError, match="Invalid artifact"):
        Artifact.from_dict({"type": "hologram", "payload": "x"})


def test_from_dict_rejects_malformed_payload():
    with pytest.raises(ValueError, match="Invalid artifact"):
        Artifact.from_dict({"type": "table", "payload": {"columns": ["a"]}})


def test_normalize_none_is_empty():
    assert normalize_artifacts(None) == []


def test_normalize_legacy_plotly_strings():
    artifacts = normalize_artifacts(['{"data": []}'])
    assert artifacts == [
        {
            "type": "plotly",
            "payload": '{"data": []}',
            "title": None,
            "role": "explanation",
            "index": 0,
        }
    ]


def test_normalize_wraps_single_values():
    assert normalize_artifacts('{"data": []}')[0]["type"] == "plotly"
    assert normalize_artifacts(TextArtifact(payload="x"))[0]["type"] == "text"


def test_normalize_artifact_instances():
    artifacts = normalize_artifacts([TextArtifact(payload="x", title="t")])
    assert artifacts == [
        {
            "type": "text",
            "payload": "x",
            "title": "t",
            "role": "explanation",
            "index": 0,
        }
    ]


def test_normalize_passes_artifact_dicts_through():
    item = {"type": "text", "payload": "x"}
    assert normalize_artifacts([item]) == [
        {
            "type": "text",
            "payload": "x",
            "title": None,
            "role": "explanation",
            "index": 0,
        }
    ]


def test_normalize_legacy_explorer_plotly():
    legacy = {"type": "plotly_json", "data": '{"data": []}', "config": {}}
    artifacts = normalize_artifacts([legacy])
    assert artifacts == [
        {
            "type": "plotly",
            "payload": '{"data": []}',
            "title": None,
            "role": "explanation",
            "index": 0,
        }
    ]


def test_normalize_legacy_explorer_tabular():
    legacy = {
        "type": "tabular",
        "data": {"a": {"r1": 1, "r2": 2}, "b": {"r1": 3, "r2": 4}},
        "config": {"orient": "dict"},
    }
    [artifact] = normalize_artifacts([legacy])
    assert artifact["type"] == "table"
    assert artifact["payload"]["columns"] == ["index", "a", "b"]
    assert artifact["payload"]["rows"] == [["r1", 1, 3], ["r2", 2, 4]]


def test_normalize_legacy_explorer_image():
    encoded = base64.b64encode(PNG_BYTES).decode("ascii")
    legacy = {"type": "image_base64", "data": encoded, "config": {}}
    [artifact] = normalize_artifacts([legacy])
    assert artifact["type"] == "image"
    assert artifact["payload"]["data"] == encoded


def test_normalize_unrenderable_falls_back_to_text():
    [artifact] = normalize_artifacts([42])
    assert artifact == {
        "type": "text",
        "payload": "42",
        "title": None,
        "role": "explanation",
        "index": 0,
    }


def test_normalize_wraps_local_explainer_items_in_grouped_artifacts():
    artifacts = normalize_artifacts(
        [
            TextArtifact(payload="x", title="Instance 1"),
            TextArtifact(payload="y", title="Instance 2"),
        ],
        create_grouped=True,
    )
    assert artifacts == [
        {
            "type": "grouped",
            "title": None,
            "groups": [
                {
                    "title": "Instance 1",
                    "artifacts": [
                        {
                            "type": "text",
                            "payload": "x",
                            "title": "Instance 1",
                            "role": "explanation",
                            "index": 0,
                        }
                    ],
                },
                {
                    "title": "Instance 2",
                    "artifacts": [
                        {
                            "type": "text",
                            "payload": "y",
                            "title": "Instance 2",
                            "role": "explanation",
                            "index": 1,
                        }
                    ],
                },
            ],
        }
    ]


def test_artifact_role_defaults_to_explanation():
    from DashAI.back.core.artifacts import TextArtifact

    artifact = TextArtifact(payload="hi")
    assert artifact.to_dict()["role"] == "explanation"


def test_artifact_role_roundtrips_input():
    from DashAI.back.core.artifacts import TableArtifact, TablePayload

    artifact = TableArtifact(
        payload=TablePayload(columns=["a"], rows=[[1]]),
        role="input",
    )
    assert artifact.to_dict()["role"] == "input"


def test_normalize_artifacts_preserves_role():
    from DashAI.back.core.artifacts import normalize_artifacts

    result = normalize_artifacts(
        [{"type": "text", "payload": "x", "title": "Instance 1", "role": "input"}]
    )
    assert result[0]["role"] == "input"


def test_build_tabular_input_artifact():
    from DashAI.back.core.artifacts import build_tabular_input_artifact

    artifact = build_tabular_input_artifact(["age", "city"], [42, "NY"], "Instance 1")
    payload = artifact.to_dict()
    assert payload["role"] == "input"
    assert payload["title"] == "Instance 1"
    assert payload["payload"]["columns"] == ["age", "city"]
    assert payload["payload"]["rows"] == [[42, "NY"]]


def test_build_text_input_artifact():
    from DashAI.back.core.artifacts import build_text_input_artifact

    artifact = build_text_input_artifact("hello world", "Instance 2")
    payload = artifact.to_dict()
    assert payload["role"] == "input"
    assert payload["type"] == "text"
    assert payload["payload"] == "hello world"


def test_build_image_input_artifact():
    from DashAI.back.core.artifacts import build_image_input_artifact
    from DashAI.back.types.dashai_image import DashAIImage

    image = DashAIImage(bytes=PNG_BYTES, path="img.png")
    artifact = build_image_input_artifact(image, "Instance 3")
    payload = artifact.to_dict()
    assert payload["role"] == "input"
    assert payload["type"] == "image"
    assert payload["title"] == "Instance 3"
