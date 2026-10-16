"""Sparse retrievers fit and reload the converter they are given."""

from DashAI.back.converters.scikit_learn.bag_of_words import BagOfWordsConverter
from DashAI.back.converters.scikit_learn.tf_idf import TFIDFConverter
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.persistence import SparsePersistence
from DashAI.back.models.RAG.retrievers.sparse.bm25_retriever import BM25Retriever
from DashAI.back.models.RAG.retrievers.sparse.tfidf_retriever import TFIDFRetriever
from tests.back.RAG.conftest import BOW_PARAMS, TFIDF_PARAMS

TEXTS = [
    "cats purr when they are happy",
    "dogs bark at the mail carrier",
    "the stock market fell sharply today",
]


def _chunks():
    return {
        1: {
            index: Chunk(id=index, document_id=1, document_position=index, text=text)
            for index, text in enumerate(TEXTS)
        }
    }


def _bm25(tmp_path):
    retriever = BM25Retriever(
        vectorizer=BagOfWordsConverter(**BOW_PARAMS),
        k1=1.5,
        b=0.75,
        delta=0.0,
        similarity_function="cosine",
        top_k=1,
    )
    retriever.inject_infra(
        str(tmp_path), _chunks(), SparsePersistence(model_dir=str(tmp_path / "bm25"))
    )
    return retriever


def _tfidf(tmp_path):
    retriever = TFIDFRetriever(
        vectorizer=TFIDFConverter(**TFIDF_PARAMS),
        similarity_function="cosine",
        top_k=1,
    )
    retriever.inject_infra(
        str(tmp_path), _chunks(), SparsePersistence(model_dir=str(tmp_path / "tfidf"))
    )
    return retriever


def test_bm25_finds_the_matching_chunk_and_reloads(tmp_path):
    fitted = _bm25(tmp_path)
    fitted.init_model()
    fitted.save()

    reloaded = _bm25(tmp_path)
    reloaded.init_model()

    assert fitted.retrieve("stock market")[0].document_position == 2
    assert reloaded.retrieve("stock market")[0].document_position == 2


def test_tfidf_finds_the_matching_chunk_and_reloads(tmp_path):
    fitted = _tfidf(tmp_path)
    fitted.init_model()
    fitted.save()

    reloaded = _tfidf(tmp_path)
    reloaded.init_model()

    assert fitted.retrieve("cats purr")[0].document_position == 0
    assert reloaded.retrieve("cats purr")[0].document_position == 0
