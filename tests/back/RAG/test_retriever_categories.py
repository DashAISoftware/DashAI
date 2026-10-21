"""Every retriever tells the frontend which group it belongs to."""

from DashAI.back.dependencies.config_builder import get_initial_components
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever

EXPECTED = {
    "BM25Retriever": "Keyword retrievers",
    "TFIDFRetriever": "Keyword retrievers",
    "DenseEmbeddingRetriever": "Dense retrievers",
    "ParallelRetriever": "Composite retrievers",
    "SequentialRetriever": "Composite retrievers",
    "MMRRerankerRetriever": "Composite retrievers",
    "SentenceTransformerCrossEncoderRetriever": "Composite retrievers",
}


def _retrievers():
    return {
        component.__name__: component
        for component in get_initial_components()
        if isinstance(component, type) and issubclass(component, BaseRetriever)
    }


def test_every_registered_retriever_has_its_category():
    retrievers = _retrievers()

    assert set(retrievers) == set(EXPECTED)
    for name, component in retrievers.items():
        assert component.get_metadata()["category"].en == EXPECTED[name], name


def test_children_endpoint_sends_localized_categories(client):
    response = client.get(
        "/api/v1/component/SparseRetriever/children/",
        params={"recursive": True},
        headers={"Accept-Language": "es"},
    )

    assert response.status_code == 200
    children = {child["name"]: child for child in response.json()}
    assert {"BM25Retriever", "TFIDFRetriever"} <= set(children)
    for name in ("BM25Retriever", "TFIDFRetriever"):
        assert (
            children[name]["metadata"]["category"] == "Recuperadores por palabras clave"
        )
        assert isinstance(children[name]["display_name"], str)


def test_categories_are_translated():
    for component in _retrievers().values():
        category = component.get_metadata()["category"]
        for language in ("es", "pt", "de", "zh"):
            assert category.get(language) != category.en, (component, language)
