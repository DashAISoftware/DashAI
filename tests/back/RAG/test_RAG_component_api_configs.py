"""Integration tests validating every RAG component configuration dimension.

Each test creates a RAG session through the API with a specific parameter
combination and verifies:

- Session creation returns 201 Created
- All parameters can be retrieved via GET and match the expected configuration

All models are ≤ 8B parameters. Larger variants (Llama-2-13B, Qwen-14B,
Mixtral, Harrier-27B, Qwen3-Embedding-8B, Meta-Llama-3.1-8B) are excluded.

Note: Session creation validates only the top-level RAGPipeline schema
({component, params} structure). Sub-component schemas are validated at
pipeline runtime, not during session creation.
"""

import pytest
from fastapi.testclient import TestClient

from tests.back.RAG.conftest import _create_test_document


@pytest.fixture(scope="module")
def test_doc_id(client: TestClient) -> int:
    """Module-scoped test document ID shared across all component config tests."""
    return _create_test_document(client, suffix="_component_configs")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

ST_MINI_LM = "sentence-transformers/all-MiniLM-L6-v2"


def _base_params(test_doc_id: int) -> dict:
    """Return the minimal default RAG session payload."""
    return {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 400, "chunk_overlap": 40},
            },
            "retriever_model": {
                "component": "BM25Retriever",
                "params": {
                    "BM25Vectorizer": {
                        "component": "BM25VectorizerModel",
                        "params": {
                            "strip_accents": None,
                            "lowercase": True,
                            "stop_words": None,
                            "max_df": 1.0,
                            "min_df": 0.0,
                            "max_features": None,
                        },
                    },
                    "k1": 1.5,
                    "b": 0.75,
                    "delta": 0.0,
                    "similarity_function": "cosine",
                    "top_k": 5,
                },
            },
            "generation_model": {
                "component": "Llama32_1BInstruct",
                "params": {
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "frequency_penalty": 0.1,
                    "context_window": 512,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Config Test",
        "description": None,
    }


def _dense_st_retriever(
    similarity_metric: str = "cosine",
    top_k: int = 10,
    model_name: str = ST_MINI_LM,
) -> dict:
    """Build a DenseEmbeddingRetriever + SentenceTransformerEmbedding config."""
    return {
        "component": "DenseEmbeddingRetriever",
        "params": {
            "embedding_model": {
                "component": "SentenceTransformerEmbedding",
                "params": {
                    "model_name": model_name,
                    "overflow_strategy": "truncate",
                    "normalize": True,
                    "device": "cpu",
                },
            },
            "similarity_metric": similarity_metric,
            "top_k": top_k,
        },
    }


def _dense_st_alt_retriever(top_k: int = 10) -> dict:
    """Build a DenseEmbeddingRetriever + SentenceTransformerEmbedding config."""
    return {
        "component": "DenseEmbeddingRetriever",
        "params": {
            "embedding_model": {
                "component": "SentenceTransformerEmbedding",
                "params": {
                    "model_name": ST_MINI_LM,
                    "overflow_strategy": "truncate",
                    "normalize": True,
                    "device": "cpu",
                },
            },
            "similarity_metric": "cosine",
            "top_k": top_k,
        },
    }


def _post_and_get(client: TestClient, params: dict):
    """POST a session, assert 201 + metadata, then GET and return stored JSON.

    NOTE: The GET response returns the raw SQLAlchemy model (serialized by
    FastAPI), which may include extra DB columns (e.g. ``user_id``) not
    present in the POST response.  This is intentional — the test verifies
    that the *stored* parameters match what was sent.
    """
    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == params["name"]
    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    return get_resp.json()


# ===================================================================
# Category 1: Encoding Models  (6 tests)
# ===================================================================


class TestEncodingModels:
    """6 configurations: sparse and dense encoding models
    with hyperparameter variations."""

    def test_encoding_bm25_default(self, client: TestClient, test_doc_id: int):
        """BM25Retriever with all default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc BM25 Default"
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "BM25Retriever"
        assert ret["params"]["k1"] == 1.5
        assert ret["params"]["b"] == 0.75
        assert ret["params"]["delta"] == 0.0
        assert ret["params"]["similarity_function"] == "cosine"
        assert ret["params"]["top_k"] == 5

    def test_encoding_bm25_custom_hyperparams(
        self, client: TestClient, test_doc_id: int
    ):
        """BM25Retriever with custom hyperparams
        k1=2.0, b=0.5, delta=0.5, euclidean, top_k=7."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc BM25 Custom"
        params["parameters"]["retriever_model"] = {
            "component": "BM25Retriever",
            "params": {
                "BM25Vectorizer": {
                    "component": "BM25VectorizerModel",
                    "params": {
                        "strip_accents": None,
                        "lowercase": True,
                        "stop_words": None,
                        "max_df": 1.0,
                        "min_df": 0.0,
                        "max_features": None,
                    },
                },
                "k1": 2.0,
                "b": 0.5,
                "delta": 0.5,
                "similarity_function": "euclidean",
                "top_k": 7,
            },
        }
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "BM25Retriever"
        assert ret["params"]["k1"] == 2.0
        assert ret["params"]["b"] == 0.5
        assert ret["params"]["delta"] == 0.5
        assert ret["params"]["similarity_function"] == "euclidean"
        assert ret["params"]["top_k"] == 7

    def test_encoding_tfidf_default(self, client: TestClient, test_doc_id: int):
        """TFIDFRetriever with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc TFIDF Default"
        params["parameters"]["retriever_model"] = {
            "component": "TFIDFRetriever",
            "params": {
                "TFIDFVectorizer": {
                    "component": "TFIDFVectorizerModel",
                    "params": {
                        "strip_accents": "None",
                        "lowercase": True,
                        "analyzer": "word",
                        "stop_words": [],
                        "ngram_range": [1, 1],
                        "max_df": 1.0,
                        "min_df": 0.0,
                        "max_features": 1000,
                        "norm": "l2",
                        "use_idf": True,
                        "smooth_idf": True,
                        "sublinear_tf": False,
                    },
                },
                "similarity_function": "cosine",
                "top_k": 5,
            },
        }
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "TFIDFRetriever"
        assert ret["params"]["similarity_function"] == "cosine"
        assert ret["params"]["top_k"] == 5

    def test_encoding_tfidf_custom(self, client: TestClient, test_doc_id: int):
        """TFIDFRetriever with similarity_function=manhattan, top_k=15."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc TFIDF Custom"
        params["parameters"]["retriever_model"] = {
            "component": "TFIDFRetriever",
            "params": {
                "TFIDFVectorizer": {
                    "component": "TFIDFVectorizerModel",
                    "params": {
                        "strip_accents": "None",
                        "lowercase": True,
                        "analyzer": "word",
                        "stop_words": [],
                        "ngram_range": [1, 1],
                        "max_df": 1.0,
                        "min_df": 0.0,
                        "max_features": 1000,
                        "norm": "l2",
                        "use_idf": True,
                        "smooth_idf": True,
                        "sublinear_tf": False,
                    },
                },
                "similarity_function": "manhattan",
                "top_k": 15,
            },
        }
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "TFIDFRetriever"
        assert ret["params"]["similarity_function"] == "manhattan"
        assert ret["params"]["top_k"] == 15

    def test_encoding_dense_sentence_transformer(
        self, client: TestClient, test_doc_id: int
    ):
        """DenseEmbeddingRetriever + SentenceTransformerEmbedding (all-MiniLM-L6-v2)."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc Dense ST"
        params["parameters"]["retriever_model"] = _dense_st_retriever(top_k=10)
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "DenseEmbeddingRetriever"
        embed = ret["params"]["embedding_model"]
        assert embed["component"] == "SentenceTransformerEmbedding"
        assert embed["params"]["model_name"] == ST_MINI_LM
        assert embed["params"]["normalize"] is True
        assert embed["params"]["device"] == "cpu"
        assert ret["params"]["similarity_metric"] == "cosine"
        assert ret["params"]["top_k"] == 10

    def test_encoding_dense_st_alt(self, client: TestClient, test_doc_id: int):
        """DenseEmbeddingRetriever + SentenceTransformerEmbedding (all-MiniLM-L6-v2)."""
        params = _base_params(test_doc_id)
        params["name"] = "Enc Dense ST Alt"
        params["parameters"]["retriever_model"] = _dense_st_alt_retriever(top_k=10)
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "DenseEmbeddingRetriever"
        embed = ret["params"]["embedding_model"]
        assert embed["component"] == "SentenceTransformerEmbedding"
        assert embed["params"]["model_name"] == ST_MINI_LM
        assert embed["params"]["normalize"] is True
        assert embed["params"]["device"] == "cpu"
        assert ret["params"]["similarity_metric"] == "cosine"
        assert ret["params"]["top_k"] == 10


# ===================================================================
# Category 2: Ranking Functions  (4 tests)
# ===================================================================


class TestRankingFunctions:
    """4 ranking function configurations evaluated with different encoding models."""

    def test_ranking_dense_cosine(self, client: TestClient, test_doc_id: int):
        """DenseEmbeddingRetriever with cosine similarity."""
        params = _base_params(test_doc_id)
        params["name"] = "Rank Cosine"
        params["parameters"]["retriever_model"] = _dense_st_retriever(
            similarity_metric="cosine", top_k=10
        )
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["params"]["similarity_metric"] == "cosine"
        assert ret["params"]["top_k"] == 10

    def test_ranking_dense_euclidean(self, client: TestClient, test_doc_id: int):
        """DenseEmbeddingRetriever with euclidean similarity."""
        params = _base_params(test_doc_id)
        params["name"] = "Rank Euclidean"
        params["parameters"]["retriever_model"] = _dense_st_retriever(
            similarity_metric="euclidean", top_k=10
        )
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["params"]["similarity_metric"] == "euclidean"
        assert ret["params"]["top_k"] == 10

    def test_ranking_sparse_manhattan(self, client: TestClient, test_doc_id: int):
        """BM25Retriever with manhattan similarity."""
        params = _base_params(test_doc_id)
        params["name"] = "Rank Manhattan"
        params["parameters"]["retriever_model"]["params"]["similarity_function"] = (
            "manhattan"
        )
        params["parameters"]["retriever_model"]["params"]["top_k"] = 10
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "BM25Retriever"  # guard: depends on _base_params
        assert ret["params"]["similarity_function"] == "manhattan"
        assert ret["params"]["top_k"] == 10

    def test_ranking_mmr_reranker(self, client: TestClient, test_doc_id: int):
        """MMRRerankerRetriever (lambda=0.7) wrapping DenseEmbeddingRetriever.

        The child's own ``top_k`` (40) defines the candidate set and the
        reranker selects ``top_k`` (10) of them.
        """
        params = _base_params(test_doc_id)
        params["name"] = "Rank MMR"
        params["parameters"]["retriever_model"] = {
            "component": "MMRRerankerRetriever",
            "params": {
                "mmr_lambda": 0.7,
                "top_k": 10,
                "children": [_dense_st_retriever(similarity_metric="cosine", top_k=40)],
            },
        }
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["component"] == "MMRRerankerRetriever"
        assert ret["params"]["mmr_lambda"] == 0.7
        assert ret["params"]["top_k"] == 10
        children = ret["params"]["children"]
        assert len(children) == 1
        assert children[0]["component"] == "DenseEmbeddingRetriever"
        assert (
            children[0]["params"]["embedding_model"]["component"]
            == "SentenceTransformerEmbedding"
        )
        assert children[0]["params"]["top_k"] == 40


# ===================================================================
# Category 3: Top K  (6 tests)
# ===================================================================


class TestTopK:
    """6 top-K configurations using different encodings and ranking functions."""

    def test_topk_bm25_3(self, client: TestClient, test_doc_id: int):
        """BM25Retriever with top_k=3."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK BM25 3"
        params["parameters"]["retriever_model"]["params"]["top_k"] = 3
        stored = _post_and_get(client, params)
        assert stored["parameters"]["retriever_model"]["params"]["top_k"] == 3

    def test_topk_tfidf_5(self, client: TestClient, test_doc_id: int):
        """TFIDFRetriever with top_k=5."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK TFIDF 5"
        params["parameters"]["retriever_model"] = {
            "component": "TFIDFRetriever",
            "params": {
                "TFIDFVectorizer": {
                    "component": "TFIDFVectorizerModel",
                    "params": {
                        "strip_accents": "None",
                        "lowercase": True,
                        "analyzer": "word",
                        "stop_words": [],
                        "ngram_range": [1, 1],
                        "max_df": 1.0,
                        "min_df": 0.0,
                        "max_features": 1000,
                        "norm": "l2",
                        "use_idf": True,
                        "smooth_idf": True,
                        "sublinear_tf": False,
                    },
                },
                "similarity_function": "cosine",
                "top_k": 5,
            },
        }
        stored = _post_and_get(client, params)
        assert stored["parameters"]["retriever_model"]["params"]["top_k"] == 5

    def test_topk_dense_st_10(self, client: TestClient, test_doc_id: int):
        """DenseEmbeddingRetriever + SentenceTransformer with top_k=10."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK Dense ST 10"
        params["parameters"]["retriever_model"] = _dense_st_retriever(top_k=10)
        stored = _post_and_get(client, params)
        assert stored["parameters"]["retriever_model"]["params"]["top_k"] == 10

    def test_topk_dense_st_15(self, client: TestClient, test_doc_id: int):
        """DenseEmbeddingRetriever + SentenceTransformerEmbedding with top_k=15."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK Dense ST 15"
        params["parameters"]["retriever_model"] = _dense_st_alt_retriever(top_k=15)
        stored = _post_and_get(client, params)
        assert stored["parameters"]["retriever_model"]["params"]["top_k"] == 15

    def test_topk_bm25_20(self, client: TestClient, test_doc_id: int):
        """BM25Retriever with top_k=20."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK BM25 20"
        params["parameters"]["retriever_model"]["params"]["top_k"] = 20
        stored = _post_and_get(client, params)
        assert stored["parameters"]["retriever_model"]["params"]["top_k"] == 20

    def test_topk_mmr_12(self, client: TestClient, test_doc_id: int):
        """MMRRerankerRetriever with top_k=12; the child retrieves 36 via its
        own top_k and the reranker selects 12."""
        params = _base_params(test_doc_id)
        params["name"] = "TopK MMR 12"
        params["parameters"]["retriever_model"] = {
            "component": "MMRRerankerRetriever",
            "params": {
                "mmr_lambda": 0.5,
                "top_k": 12,
                "children": [_dense_st_retriever(similarity_metric="cosine", top_k=36)],
            },
        }
        stored = _post_and_get(client, params)
        ret = stored["parameters"]["retriever_model"]
        assert ret["params"]["top_k"] == 12
        assert ret["params"]["children"][0]["params"]["top_k"] == 36


# ===================================================================
# Category 4: Chunking Strategies  (6 tests)
# ===================================================================


class TestChunkingStrategies:
    """6 chunking strategy configurations with different algorithms
    and parameters (chunk_size, chunk_overlap)."""

    def test_chunking_char_small(self, client: TestClient, test_doc_id: int):
        """CharacterChunkModel with chunk_size=256, chunk_overlap=25."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Char 256/25"
        params["parameters"]["chunking_model"] = {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 256, "chunk_overlap": 25},
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "CharacterChunkModel"
        assert chunk["params"]["chunk_size"] == 256
        assert chunk["params"]["chunk_overlap"] == 25

    def test_chunking_char_paragraph(self, client: TestClient, test_doc_id: int):
        """CharacterChunkModel with chunk_size=500, chunk_overlap=50."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Char 500/50"
        params["parameters"]["chunking_model"] = {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 500, "chunk_overlap": 50},
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "CharacterChunkModel"
        assert chunk["params"]["chunk_size"] == 500
        assert chunk["params"]["chunk_overlap"] == 50

    def test_chunking_char_page(self, client: TestClient, test_doc_id: int):
        """CharacterChunkModel with chunk_size=2000, chunk_overlap=200."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Char 2000/200"
        params["parameters"]["chunking_model"] = {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 2000, "chunk_overlap": 200},
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "CharacterChunkModel"
        assert chunk["params"]["chunk_size"] == 2000
        assert chunk["params"]["chunk_overlap"] == 200

    def test_chunking_recursive_custom(self, client: TestClient, test_doc_id: int):
        """RecursiveCharacterChunkModel with custom separators."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Recursive Custom"
        params["parameters"]["chunking_model"] = {
            "component": "RecursiveCharacterChunkModel",
            "params": {
                "chunk_size": 1000,
                "chunk_overlap": 100,
                "separators": ["\n\n", "\n", ".", " ", ""],
            },
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "RecursiveCharacterChunkModel"
        assert chunk["params"]["chunk_size"] == 1000
        assert chunk["params"]["chunk_overlap"] == 100
        assert chunk["params"]["separators"] == ["\n\n", "\n", ".", " ", ""]

    def test_chunking_token_e5_mistral(self, client: TestClient, test_doc_id: int):
        """TokenChunkModel with e5-mistral tokenizer, chunk_size=300, overlap=60."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Token E5"
        params["parameters"]["chunking_model"] = {
            "component": "TokenChunkModel",
            "params": {
                "tokenizer_name": "intfloat/e5-mistral-7b-instruct",
                "chunk_size": 300,
                "chunk_overlap": 60,
            },
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "TokenChunkModel"
        assert chunk["params"]["tokenizer_name"] == "intfloat/e5-mistral-7b-instruct"
        assert chunk["params"]["chunk_size"] == 300
        assert chunk["params"]["chunk_overlap"] == 60

    def test_chunking_token_bert_spanish(self, client: TestClient, test_doc_id: int):
        """TokenChunkModel with BERT Spanish tokenizer, chunk_size=512, overlap=50."""
        params = _base_params(test_doc_id)
        params["name"] = "Chunk Token BERT ES"
        params["parameters"]["chunking_model"] = {
            "component": "TokenChunkModel",
            "params": {
                "tokenizer_name": "dccuchile/bert-base-spanish-wwm-uncased",
                "chunk_size": 512,
                "chunk_overlap": 50,
            },
        }
        stored = _post_and_get(client, params)
        chunk = stored["parameters"]["chunking_model"]
        assert chunk["component"] == "TokenChunkModel"
        assert (
            chunk["params"]["tokenizer_name"]
            == "dccuchile/bert-base-spanish-wwm-uncased"
        )
        assert chunk["params"]["chunk_size"] == 512
        assert chunk["params"]["chunk_overlap"] == 50


# ===================================================================
# Category 5: Prompts  (4 tests)
# ===================================================================


class TestPrompts:
    """4 prompt configurations validating formatting and chat session consistency."""

    def test_prompt_default_rag_en(self, client: TestClient, test_doc_id: int):
        """DefaultRAGGenerationPrompt with language=en."""
        params = _base_params(test_doc_id)
        params["name"] = "Prompt RAG EN"
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt"
        assert prompt["params"]["language"] == "en"

    def test_prompt_default_rag_es(self, client: TestClient, test_doc_id: int):
        """DefaultRAGGenerationPrompt with language=es."""
        params = _base_params(test_doc_id)
        params["name"] = "Prompt RAG ES"
        params["parameters"]["prompt"] = {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "es"},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt"
        assert prompt["params"]["language"] == "es"

    def test_prompt_default_qna_en(self, client: TestClient, test_doc_id: int):
        """DefaultQARAGGenerationPrompt with language=en."""
        params = _base_params(test_doc_id)
        params["name"] = "Prompt QnA EN"
        params["parameters"]["prompt"] = {
            "component": "DefaultQARAGGenerationPrompt",
            "params": {"language": "en"},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultQARAGGenerationPrompt"
        assert prompt["params"]["language"] == "en"

    def test_prompt_custom_template(self, client: TestClient, test_doc_id: int):
        """CustomRAGGenerationPrompt with user-defined template."""
        template_text = "Answer the question based on: {chunks}\n\nQuestion: {input}"
        params = _base_params(test_doc_id)
        params["name"] = "Prompt Custom"
        params["parameters"]["prompt"] = {
            "component": "CustomRAGGenerationPrompt",
            "params": {"template": template_text},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "CustomRAGGenerationPrompt"
        assert prompt["params"]["template"] == template_text


# ===================================================================
# Category 6: Generator Models  (8 tests)
# ===================================================================


class TestGeneratorModels:
    """8 generator model configurations with different models
    and hyperparameters (≤8B)."""

    def test_generator_llama_1b_default(self, client: TestClient, test_doc_id: int):
        """Llama 3.2-1B with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Llama 1B Default"
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Llama32_1BInstruct"
        assert gen["params"]["max_tokens"] == 100
        assert gen["params"]["temperature"] == 0.7
        assert gen["params"]["frequency_penalty"] == 0.1
        assert gen["params"]["context_window"] == 512
        assert gen["params"]["device"] == "CPU"

    def test_generator_llama_3b_custom(self, client: TestClient, test_doc_id: int):
        """Llama 3.2-3B with custom hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Llama 3B Custom"
        params["parameters"]["generation_model"] = {
            "component": "Llama32_3BInstruct",
            "params": {
                "max_tokens": 512,
                "temperature": 0.5,
                "frequency_penalty": 0.0,
                "context_window": 2048,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Llama32_3BInstruct"
        assert gen["params"]["max_tokens"] == 512
        assert gen["params"]["temperature"] == 0.5
        assert gen["params"]["frequency_penalty"] == 0.0
        assert gen["params"]["context_window"] == 2048
        assert gen["params"]["device"] == "CPU"

    def test_generator_mistral_7b_default(self, client: TestClient, test_doc_id: int):
        """Mistral 7B v0.3 with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Mistral 7B Default"
        params["parameters"]["generation_model"] = {
            "component": "Mistral7BInstructV03",
            "params": {
                "max_tokens": 100,
                "temperature": 0.7,
                "frequency_penalty": 0.1,
                "context_window": 512,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Mistral7BInstructV03"
        assert gen["params"]["max_tokens"] == 100
        assert gen["params"]["temperature"] == 0.7
        assert gen["params"]["frequency_penalty"] == 0.1
        assert gen["params"]["context_window"] == 512
        assert gen["params"]["device"] == "CPU"

    def test_generator_qwen_0_5b_default(self, client: TestClient, test_doc_id: int):
        """Qwen 2.5-0.5B with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Qwen 0.5B Default"
        params["parameters"]["generation_model"] = {
            "component": "Qwen25_05BInstruct",
            "params": {
                "max_tokens": 100,
                "temperature": 0.7,
                "frequency_penalty": 0.1,
                "context_window": 512,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Qwen25_05BInstruct"
        assert gen["params"]["max_tokens"] == 100
        assert gen["params"]["temperature"] == 0.7
        assert gen["params"]["frequency_penalty"] == 0.1
        assert gen["params"]["context_window"] == 512
        assert gen["params"]["device"] == "CPU"

    def test_generator_qwen_1_5b_custom(self, client: TestClient, test_doc_id: int):
        """Qwen 2.5-1.5B with custom hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Qwen 1.5B Custom"
        params["parameters"]["generation_model"] = {
            "component": "Qwen25_15BInstruct",
            "params": {
                "max_tokens": 256,
                "temperature": 0.3,
                "frequency_penalty": 0.5,
                "context_window": 1024,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Qwen25_15BInstruct"
        assert gen["params"]["max_tokens"] == 256
        assert gen["params"]["temperature"] == 0.3
        assert gen["params"]["frequency_penalty"] == 0.5
        assert gen["params"]["context_window"] == 1024
        assert gen["params"]["device"] == "CPU"

    def test_generator_smol_1_7b_default(self, client: TestClient, test_doc_id: int):
        """SmolLM2 1.7B with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen SmolLM 1.7B Default"
        params["parameters"]["generation_model"] = {
            "component": "SmolLM2_17BInstruct",
            "params": {
                "max_tokens": 100,
                "temperature": 0.7,
                "frequency_penalty": 0.1,
                "context_window": 512,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "SmolLM2_17BInstruct"
        assert gen["params"]["max_tokens"] == 100
        assert gen["params"]["temperature"] == 0.7
        assert gen["params"]["frequency_penalty"] == 0.1
        assert gen["params"]["context_window"] == 512
        assert gen["params"]["device"] == "CPU"

    def test_generator_phi4_mini_default(self, client: TestClient, test_doc_id: int):
        """Phi4MiniInstructModel with default hyperparams."""
        params = _base_params(test_doc_id)
        params["name"] = "Gen Phi4 Mini Default"
        params["parameters"]["generation_model"] = {
            "component": "Phi4MiniInstructModel",
            "params": {
                "model_name": "unsloth/Phi-4-mini-instruct-GGUF",
                "quantization": "Phi-4-mini-instruct-Q4_K_M.gguf",
                "max_tokens": 100,
                "temperature": 0.7,
                "frequency_penalty": 0.1,
                "context_window": 512,
                "device": "CPU",
            },
        }
        stored = _post_and_get(client, params)
        gen = stored["parameters"]["generation_model"]
        assert gen["component"] == "Phi4MiniInstructModel"
        assert gen["params"]["model_name"] == "unsloth/Phi-4-mini-instruct-GGUF"
        assert gen["params"]["max_tokens"] == 100
        assert gen["params"]["temperature"] == 0.7
        assert gen["params"]["frequency_penalty"] == 0.1
        assert gen["params"]["context_window"] == 512
        assert gen["params"]["device"] == "CPU"
