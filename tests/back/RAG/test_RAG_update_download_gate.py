"""Choosing a retriever through the parameter update is gated on downloads."""

import pytest
from fastapi.testclient import TestClient

from DashAI.back.converters.hugging_face.text_embedding import TextEmbeddingConverter
from tests.back.RAG.conftest import _create_holder_session

DENSE_RETRIEVER = {
    "component": "DenseEmbeddingRetriever",
    "params": {
        "embedding_model": {
            "component": "MultilingualE5SmallEmbedding",
            "params": {
                "device": "CPU",
                "batch_size": 32,
                "normalize": True,
                "overflow_strategy": "truncate",
            },
        },
        "similarity_metric": "cosine",
        "top_k": 5,
    },
}


@pytest.fixture
def embeddings_not_downloaded(monkeypatch):
    """Undo the suite wide fixture: the embedding is not on disk."""
    monkeypatch.setattr(
        TextEmbeddingConverter, "is_downloaded", classmethod(lambda cls: False)
    )


def test_updating_to_an_undownloaded_embedding_returns_409(
    client: TestClient, embeddings_not_downloaded
):
    session_id = _create_holder_session(client, "update_download_gate_blocked")

    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={"retriever_model": DENSE_RETRIEVER},
    )

    assert response.status_code == 409, response.text
    assert "must be downloaded" in response.json()["detail"]
    assert "MultilingualE5SmallEmbedding" in response.json()["detail"]


def test_updating_to_a_downloaded_embedding_succeeds(client: TestClient):
    session_id = _create_holder_session(client, "update_download_gate_allowed")

    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={"retriever_model": DENSE_RETRIEVER},
    )

    assert response.status_code == 200, response.text
