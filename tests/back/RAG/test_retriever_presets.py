"""Tests for the retriever-presets endpoint."""

from fastapi.testclient import TestClient


def test_retriever_presets_returns_three_presets(client: TestClient):
    response = client.get("/api/v1/rag/retriever-presets", params={"top_k": 10})
    assert response.status_code == 200
    data = response.json()
    assert [p["key"] for p in data] == ["keyword", "semantic", "hybrid"]


def test_keyword_preset(client: TestClient):
    data = client.get("/api/v1/rag/retriever-presets", params={"top_k": 10}).json()
    keyword = data[0]
    assert keyword["component"] == "BM25Retriever"
    assert keyword["params"]["top_k"] == 10
    assert keyword["params"]["BM25Vectorizer"]["component"] == "BM25VectorizerModel"
    assert "k1" in keyword["params"]


def test_semantic_preset(client: TestClient):
    data = client.get("/api/v1/rag/retriever-presets", params={"top_k": 10}).json()
    semantic = data[1]
    assert semantic["component"] == "DenseEmbeddingRetriever"
    assert semantic["params"]["top_k"] == 10
    emb = semantic["params"]["embedding_model"]
    assert emb["component"] == "SentenceTransformerEmbedding"
    assert emb["params"]["model_name"] == (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def test_hybrid_preset_splits_top_k(client: TestClient):
    data = client.get("/api/v1/rag/retriever-presets", params={"top_k": 15}).json()
    hybrid = data[2]
    assert hybrid["component"] == "ParallelRetriever"
    assert hybrid["params"]["merge_strategy"] == "round_robin"
    children = hybrid["params"]["children"]
    assert children[0]["component"] == "BM25Retriever"
    assert children[0]["params"]["top_k"] == 8  # ceil(15/2)
    assert children[1]["component"] == "DenseEmbeddingRetriever"
    assert children[1]["params"]["top_k"] == 7  # floor(15/2)


def test_retriever_presets_rejects_invalid_top_k(client: TestClient):
    response = client.get("/api/v1/rag/retriever-presets", params={"top_k": 0})
    assert response.status_code == 422
