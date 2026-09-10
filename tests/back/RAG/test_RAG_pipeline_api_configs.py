"""Integration tests validating RAG pipeline configurations from published research.

Each test creates a RAG session through the API with the exact parameter set
specified in the referenced publications and verifies:

- Session creation returns 201 Created
- Model name ("RAGPipeline") and task name ("RAGTask") are correct
- All parameters can be retrieved via GET and match the expected configuration

Note: Session creation validates only the top-level RAGPipeline schema
({component, params} structure). Sub-component schemas (Llama32_3BInstruct,
SentenceTransformerEmbedding, etc.) are validated at pipeline runtime, not during
session creation.
"""

import pytest
from fastapi.testclient import TestClient

from tests.back.RAG.conftest import _create_test_document

ST_MINI_LM = "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture(scope="module")
def test_doc_id(client: TestClient) -> int:
    """Module-scoped test document ID shared across all pipeline config tests."""
    return _create_test_document(client, suffix="_pipeline_configs")


def test_publication_1_medical_fitness(client: TestClient, test_doc_id: int):
    """Retrieval augmented generation for 10 large language models and its
    generalizability in assessing medical fitness.

    Configuration:
    - Chunking:  RecursiveCharacterChunkModel (1000/100)
    - Retrieval: DenseEmbeddingRetriever + SentenceTransformerEmbedding
      (all-MiniLM-L6-v2, cosine, top_k=10)
    - Prompt:    DefaultRAGGenerationPrompt (en)
    - Generator: Llama 3.2-3B (1024 tokens, temp 0.1)
    """
    params = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "RecursiveCharacterChunkModel",
                "params": {
                    "chunk_size": 1000,
                    "chunk_overlap": 100,
                    "separators": ["\n\n", "\n", ".", " ", ""],
                },
            },
            "retriever_model": {
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
                    "top_k": 10,
                },
            },
            "generation_model": {
                "component": "Llama32_3BInstruct",
                "params": {
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "frequency_penalty": 0.0,
                    "context_window": 4096,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Pub 1 - Medical Fitness",
        "description": None,
    }

    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == "Pub 1 - Medical Fitness"

    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    stored = get_resp.json()
    chunking = stored["parameters"]["chunking_model"]
    retriever = stored["parameters"]["retriever_model"]
    assert chunking["component"] == "RecursiveCharacterChunkModel"
    assert retriever["component"] == "DenseEmbeddingRetriever"
    assert (
        retriever["params"]["embedding_model"]["component"]
        == "SentenceTransformerEmbedding"
    )
    assert stored["parameters"]["generation_model"]["component"] == "Llama32_3BInstruct"
    assert stored["parameters"]["prompt"]["component"] == "DefaultRAGGenerationPrompt"


def test_publication_2_ehr_summarization(client: TestClient, test_doc_id: int):
    """Applying generative AI with retrieval augmented generation to summarize
    and extract key clinical information from electronic health records.

    Configuration:
    - Chunking:  CharacterChunkModel (600/40)
    - Retrieval: MMRRerankerRetriever (lambda=0.5) wrapping
                 DenseEmbeddingRetriever + SentenceTransformerEmbedding
                 (all-MiniLM-L6-v2, cosine, retrieval top_k=60)
    - Prompt:    DefaultRAGGenerationPrompt (en)
    - Generator: Llama 3.2-3B
    """
    mname = ST_MINI_LM
    params = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 600, "chunk_overlap": 40},
            },
            "retriever_model": {
                "component": "MMRRerankerRetriever",
                "params": {
                    "mmr_lambda": 0.5,
                    "top_k": 20,
                    "children": [
                        {
                            "component": "DenseEmbeddingRetriever",
                            "params": {
                                "embedding_model": {
                                    "component": "SentenceTransformerEmbedding",
                                    "params": {
                                        "model_name": mname,
                                        "overflow_strategy": "truncate",
                                        "normalize": True,
                                        "device": "cpu",
                                    },
                                },
                                "similarity_metric": "cosine",
                                "top_k": 60,
                            },
                        }
                    ],
                },
            },
            "generation_model": {
                "component": "Llama32_3BInstruct",
                "params": {
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "frequency_penalty": 0.0,
                    "context_window": 4096,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Pub 2 - EHR Summarization",
        "description": None,
    }

    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == "Pub 2 - EHR Summarization"

    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    stored = get_resp.json()
    assert stored["parameters"]["chunking_model"]["component"] == "CharacterChunkModel"
    assert (
        stored["parameters"]["retriever_model"]["component"] == "MMRRerankerRetriever"
    )
    assert stored["parameters"]["generation_model"]["component"] == "Llama32_3BInstruct"
    assert stored["parameters"]["prompt"]["component"] == "DefaultRAGGenerationPrompt"

    # Verify the MMRRerankerRetriever wraps a DenseEmbeddingRetriever child
    retriever = stored["parameters"]["retriever_model"]
    children = retriever["params"]["children"]
    assert len(children) == 1
    assert children[0]["component"] == "DenseEmbeddingRetriever"
    assert (
        children[0]["params"]["embedding_model"]["component"]
        == "SentenceTransformerEmbedding"
    )


def test_publication_3_case_study(client: TestClient, test_doc_id: int):
    """Development and Testing of Retrieval Augmented Generation in Large
    Language Models -- A Case Study Report.

    Same retriever and chunking configuration as the medical fitness study
    but with Llama 3.2-1B (smaller model).

    Configuration:
    - Chunking:  RecursiveCharacterChunkModel (1000/100)
    - Retrieval: DenseEmbeddingRetriever + SentenceTransformerEmbedding
      (all-MiniLM-L6-v2, cosine, top_k=10)
    - Prompt:    DefaultRAGGenerationPrompt (en)
    - Generator: Llama 3.2-1B
    """
    params = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "RecursiveCharacterChunkModel",
                "params": {
                    "chunk_size": 1000,
                    "chunk_overlap": 100,
                    "separators": ["\n\n", "\n", ".", " ", ""],
                },
            },
            "retriever_model": {
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
                    "top_k": 10,
                },
            },
            "generation_model": {
                "component": "Llama32_1BInstruct",
                "params": {
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "frequency_penalty": 0.0,
                    "context_window": 4096,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Pub 3 - Case Study",
        "description": None,
    }

    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == "Pub 3 - Case Study"

    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    stored = get_resp.json()
    chunking = stored["parameters"]["chunking_model"]
    retriever = stored["parameters"]["retriever_model"]
    assert chunking["component"] == "RecursiveCharacterChunkModel"
    assert retriever["component"] == "DenseEmbeddingRetriever"
    assert (
        retriever["params"]["embedding_model"]["component"]
        == "SentenceTransformerEmbedding"
    )
    gen = stored["parameters"]["generation_model"]
    assert gen["component"] == "Llama32_1BInstruct"


def test_publication_4a_ragchecker_dense(client: TestClient, test_doc_id: int):
    """RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented
    Generation (dense variant).

    Configuration:
    - Chunking:  TokenChunkModel (300/60, e5-mistral tokenizer)
    - Retrieval: DenseEmbeddingRetriever + SentenceTransformerEmbedding
                 (all-MiniLM-L6-v2, cosine, top_k=20)
    - Prompt:    DefaultRAGGenerationPrompt (en)
    - Generator: Llama 3.2-3B
    """
    params = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "TokenChunkModel",
                "params": {
                    "tokenizer_name": "intfloat/e5-mistral-7b-instruct",
                    "chunk_size": 300,
                    "chunk_overlap": 60,
                },
            },
            "retriever_model": {
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
                    "top_k": 20,
                },
            },
            "generation_model": {
                "component": "Llama32_3BInstruct",
                "params": {
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "frequency_penalty": 0.0,
                    "context_window": 4096,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Pub 4a - RAGChecker Dense",
        "description": None,
    }

    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == "Pub 4a - RAGChecker Dense"

    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    stored = get_resp.json()
    assert stored["parameters"]["chunking_model"]["component"] == "TokenChunkModel"
    retriever = stored["parameters"]["retriever_model"]
    assert retriever["component"] == "DenseEmbeddingRetriever"
    embed = retriever["params"]["embedding_model"]
    assert embed["component"] == "SentenceTransformerEmbedding"
    assert embed["params"]["model_name"] == ST_MINI_LM
    assert retriever["params"]["top_k"] == 20
    assert stored["parameters"]["generation_model"]["component"] == "Llama32_3BInstruct"


def test_publication_4b_ragchecker_sparse(client: TestClient, test_doc_id: int):
    """RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented
    Generation (sparse variant).

    Same as 4a but with BM25Retriever instead of DenseEmbeddingRetriever.

    Configuration:
    - Chunking:  TokenChunkModel (300/60, e5-mistral tokenizer)
    - Retrieval: BM25Retriever (cosine, top_k=20, k1=1.5, b=0.75)
    - Prompt:    DefaultRAGGenerationPrompt (en)
    - Generator: Llama 3.2-3B
    """
    params = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "TokenChunkModel",
                "params": {
                    "tokenizer_name": "intfloat/e5-mistral-7b-instruct",
                    "chunk_size": 300,
                    "chunk_overlap": 60,
                },
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
                    "similarity_function": "cosine",
                    "top_k": 20,
                    "k1": 1.5,
                    "b": 0.75,
                    "delta": 0.0,
                },
            },
            "generation_model": {
                "component": "Llama32_3BInstruct",
                "params": {
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "frequency_penalty": 0.0,
                    "context_window": 4096,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
        "name": "Pub 4b - RAGChecker Sparse",
        "description": None,
    }

    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == "Pub 4b - RAGChecker Sparse"

    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    stored = get_resp.json()
    assert stored["parameters"]["chunking_model"]["component"] == "TokenChunkModel"
    retriever = stored["parameters"]["retriever_model"]
    assert retriever["component"] == "BM25Retriever"
    assert retriever["params"]["top_k"] == 20
    assert retriever["params"]["k1"] == 1.5
    assert retriever["params"]["b"] == 0.75
    assert stored["parameters"]["generation_model"]["component"] == "Llama32_3BInstruct"
