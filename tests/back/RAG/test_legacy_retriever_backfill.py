"""Startup conversion of RAG retrievers saved by earlier versions."""

import copy

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.dependencies.config_builder import get_initial_components
from DashAI.back.dependencies.database.backfill import backfill_rag_retrievers
from DashAI.back.dependencies.database.models import Base, GenerativeSession
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.services.RAG.legacy_retrievers import translate_legacy_retriever
from DashAI.back.services.RAG.session_validation_service import (
    SessionValidationService,
)

# The retrievers exactly as v0.10.0 stored them.
LEGACY_BM25 = {
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
        "top_k": 10,
    },
}
LEGACY_TFIDF = {
    "component": "TFIDFRetriever",
    "params": {
        "TFIDFVectorizer": {
            "component": "TFIDFVectorizerModel",
            "params": {
                "strip_accents": "None",
                "lowercase": True,
                "analyzer": "word",
                "stop_words": ["el", "la"],
                "ngram_range": [1, 2],
                "max_df": 1.0,
                "min_df": 0.0,
                "max_features": 1000,
                "norm": "None",
                "use_idf": True,
                "smooth_idf": True,
                "sublinear_tf": False,
            },
        },
        "similarity_function": "cosine",
        "top_k": 7,
    },
}
LEGACY_SEMANTIC = {
    "component": "DenseEmbeddingRetriever",
    "params": {
        "embedding_model": {
            "component": "SentenceTransformerEmbedding",
            "params": {
                "model_name": (
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                ),
                "overflow_strategy": "aggregate",
                "normalize": False,
                "device": "cpu",
            },
        },
        "similarity_metric": "cosine",
        "top_k": 10,
    },
}
LEGACY_BERT = {
    "component": "DenseEmbeddingRetriever",
    "params": {
        "embedding_model": {
            "component": "BERTEmbedding",
            "params": {
                "model_name": "google-bert/bert-base-cased",
                "overflow_strategy": "truncate",
                "device": "cpu",
                "pooling_strategy": "mean",
            },
        },
        "similarity_metric": "cosine",
        "top_k": 5,
    },
}


@pytest.fixture(scope="module", name="registry")
def fixture_registry():
    return ComponentRegistry(initial_components=get_initial_components())


@pytest.fixture(name="factory")
def fixture_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'retrievers.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def _validated(retriever, registry):
    """Translate a retriever and validate it as a parameter update would.

    Parameters
    ----------
    retriever : dict
        A stored ``retriever_model`` reference.
    registry : ComponentRegistry
        Registry of the current components.

    Returns
    -------
    dict
        The translated and validated reference.
    """
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        translated = translate_legacy_retriever(retriever, registry)
        return SessionValidationService(db, registry).validate_update_payload(
            {"retriever_model": translated}
        )["retriever_model"]


def _session(factory, name, retriever) -> int:
    """Insert a RAG session with a stored retriever.

    Parameters
    ----------
    factory : sessionmaker
        Session factory of the test database.
    name : str
        Session name.
    retriever : dict
        Its ``retriever_model``.

    Returns
    -------
    int
        The session id.
    """
    with factory() as db:
        session = GenerativeSession(
            name=name,
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": [], "retriever_model": copy.deepcopy(retriever)},
        )
        db.add(session)
        db.commit()
        return session.id


def test_the_default_bm25_vectorizer_becomes_bag_of_words(registry):
    retriever = _validated(LEGACY_BM25, registry)

    assert retriever["component"] == "BM25Retriever"
    assert "BM25Vectorizer" not in retriever["params"]
    vectorizer = retriever["params"]["vectorizer"]
    assert vectorizer["component"] == "BagOfWordsConverter"
    assert vectorizer["params"]["max_features"] is None
    assert vectorizer["params"]["lowercase"] is True
    assert retriever["params"]["top_k"] == 10


def test_tfidf_options_keep_their_meaning(registry):
    vectorizer = _validated(LEGACY_TFIDF, registry)["params"]["vectorizer"]

    assert vectorizer["component"] == "TFIDFConverter"
    params = vectorizer["params"]
    assert params["custom_stop_words"] == ["el", "la"]
    assert params["stop_words"] is None
    assert (params["lower_bound_ngrams"], params["upper_bound_ngrams"]) == (1, 2)
    assert params["strip_accents"] is None
    assert params["norm"] is None


def test_an_embedding_model_moves_to_its_converter(registry):
    embedding = _validated(LEGACY_SEMANTIC, registry)["params"]["embedding_model"]

    assert embedding["component"] == "ParaphraseMultilingualMiniLML12V2Embedding"
    assert embedding["params"]["device"] == "CPU"
    assert embedding["params"]["overflow_strategy"] == "aggregate"
    assert embedding["params"]["normalize"] is False


def test_composite_children_are_translated(registry):
    hybrid = {
        "component": "ParallelRetriever",
        "params": {
            "merge_strategy": "round_robin",
            "children": [LEGACY_BM25, LEGACY_SEMANTIC],
        },
    }

    children = _validated(hybrid, registry)["params"]["children"]

    assert children[0]["params"]["vectorizer"]["component"] == "BagOfWordsConverter"
    assert (
        children[1]["params"]["embedding_model"]["component"]
        == "ParaphraseMultilingualMiniLML12V2Embedding"
    )


def test_a_model_no_converter_serves_is_left_alone(registry):
    translated = translate_legacy_retriever(LEGACY_BERT, registry)

    assert (
        translated["params"]["embedding_model"]
        == (LEGACY_BERT["params"]["embedding_model"])
    )


def test_the_backfill_saves_only_retrievers_that_validate(factory, registry):
    legacy = _session(factory, "legacy", LEGACY_BM25)
    unserved = _session(factory, "unserved", LEGACY_BERT)
    current = _validated(LEGACY_SEMANTIC, registry)
    up_to_date = _session(factory, "current", current)

    backfill_rag_retrievers(factory, registry)
    backfill_rag_retrievers(factory, registry)

    with factory() as db:
        validator = SessionValidationService(db, registry)
        converted = db.get(GenerativeSession, legacy)
        validator.validate_stored_retriever(converted.parameters)
        assert converted.needs_reindex is True
        kept = db.get(GenerativeSession, unserved)
        assert kept.parameters["retriever_model"] == LEGACY_BERT
        assert kept.needs_reindex is False
        untouched = db.get(GenerativeSession, up_to_date)
        assert untouched.parameters["retriever_model"] == current
        assert untouched.needs_reindex is False
