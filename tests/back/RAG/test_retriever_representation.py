"""Tests for the per-retriever representation template in component metadata."""

import re
from typing import Any, Dict, Tuple

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever

#: Matches a representation placeholder such as ``{top_k}`` or
#: ``{embedding_model.model_name}``.
PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")

#: Expected placeholders in each concrete retriever's English template.
REPRESENTATION_PLACEHOLDERS: Dict[str, Tuple[str, ...]] = {
    "BM25Retriever": ("{k1}", "{b}", "{top_k}"),
    "TFIDFRetriever": ("{similarity_function}", "{top_k}"),
    "DenseEmbeddingRetriever": (
        "{embedding_model.model_name}",
        "{similarity_metric}",
        "{top_k}",
    ),
    "SentenceTransformerCrossEncoderRetriever": ("{model_name}", "{top_k}"),
    "MMRRerankerRetriever": ("{mmr_lambda}", "{top_k}"),
    "ParallelRetriever": ("{merge_strategy}",),
    "LLMEvaluatedDepthRetriever": ("{max_iters}", "{max_chunks}", "{prompt}"),
    "LLMEvaluatedEnsembleRetriever": ("{max_iters}", "{max_chunks}", "{prompt}"),
}

LANGUAGES = ("en", "es", "pt", "de", "zh")


def _representation(client: TestClient, component_name: str) -> MultilingualString:
    """Return a registered retriever's representation template."""
    registry = client.app.container["component_registry"]
    return registry[component_name]["metadata"]["representation"]


def _schema_properties(registry: Any, component_name: str) -> Dict[str, Any]:
    """Return the top-level properties of a registered component's schema."""
    return registry[component_name]["schema"].get("properties", {})


def _assert_placeholders_resolve(
    registry: Any, component_name: str, template: str
) -> None:
    """Assert every placeholder maps to a real schema parameter.

    A direct token (``{top_k}``) must name a retriever parameter. A nested
    token (``{embedding_model.model_name}``) must name a component parameter
    and a field present in that nested component's schema.
    """
    properties = _schema_properties(registry, component_name)
    for token in PLACEHOLDER_PATTERN.findall(template):
        path = [part for part in token.split(".") if part]
        assert path, f"Empty placeholder in {component_name}: {token!r}"
        assert path[0] in properties, (
            f"{component_name} placeholder {token!r} does not match a schema "
            f"parameter; available: {sorted(properties)}."
        )
        if len(path) == 1:
            continue

        nested_property = properties[path[0]]
        nested_component = (nested_property.get("placeholder") or {}).get("component")
        assert nested_component in registry, (
            f"{component_name} placeholder {token!r} has no resolvable nested "
            f"component (found {nested_component!r})."
        )
        nested_properties = _schema_properties(registry, nested_component)
        assert path[1] in nested_properties, (
            f"{component_name} placeholder {token!r} does not match a "
            f"{nested_component} parameter; available: {sorted(nested_properties)}."
        )


def test_base_retriever_has_no_representation():
    """The abstract base declares no template and omits it from metadata."""
    assert BaseRetriever.get_representation() is None
    assert "representation" not in BaseRetriever.get_metadata()


@pytest.mark.parametrize(
    ("component_name", "placeholders"),
    REPRESENTATION_PLACEHOLDERS.items(),
)
def test_registered_retriever_declares_representation(
    client: TestClient,
    component_name: str,
    placeholders: Tuple[str, ...],
):
    """Every concrete retriever exposes a multilingual template with its params."""
    representation = _representation(client, component_name)
    registry = client.app.container["component_registry"]

    assert isinstance(representation, MultilingualString)
    for language in LANGUAGES:
        template = getattr(representation, language)
        assert template, f"{component_name} is missing its {language} template"
        for placeholder in placeholders:
            assert placeholder in template
        _assert_placeholders_resolve(registry, component_name, template)


def test_llm_representation_labels_are_translated(client: TestClient):
    """The LLM templates carry translated labels, not just placeholders."""
    representation = _representation(client, "LLMEvaluatedDepthRetriever")

    expected_labels = {
        "en": ("max_iters", "max_chunks"),
        "es": ("máx. iteraciones", "máx. fragmentos"),
        "pt": ("máx. iterações", "máx. trechos"),
        "de": ("max. Iterationen", "max. Chunks"),
        "zh": ("最大迭代", "最大片段"),
    }
    for language, labels in expected_labels.items():
        template = getattr(representation, language)
        for label in labels:
            assert label in template


def test_children_endpoint_serializes_the_representation(client: TestClient):
    """The endpoint consumed by the frontend returns a language map."""
    response = client.get(
        "/api/v1/component/BaseRetriever/children", params={"recursive": True}
    )
    assert response.status_code == 200

    entries = {entry["name"]: entry for entry in response.json()}
    metadata = entries["LLMEvaluatedDepthRetriever"]["metadata"]
    representation = metadata["representation"]

    assert set(representation) == set(LANGUAGES)
    assert representation["en"] == (
        "max_iters {max_iters} · max_chunks {max_chunks} · {prompt}"
    )
    assert "operation_summary" not in metadata


def test_sequential_retriever_has_no_representation(client: TestClient):
    """Sequential falls back to its component description in the frontend."""
    registry = client.app.container["component_registry"]

    assert registry["SequentialRetriever"]["class"].get_representation() is None
    assert "representation" not in registry["SequentialRetriever"]["metadata"]


def test_metadata_representation_is_the_declared_template(client: TestClient):
    """Metadata exposes the very object returned by ``get_representation``."""
    registry = client.app.container["component_registry"]
    component_class = registry["BM25Retriever"]["class"]

    assert (
        component_class.get_metadata()["representation"]
        is component_class.get_representation()
    )


def test_no_registered_retriever_exposes_operation_summary(client: TestClient):
    """The superseded ``operation_summary`` metadata is gone everywhere."""
    registry = client.app.container["component_registry"]

    for entry in registry.get_components_by_types("Retriever"):
        assert "operation_summary" not in (entry["metadata"] or {})
