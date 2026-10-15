"""Dense retrievers embed passages and queries with an embedding converter."""

import numpy as np

from DashAI.back.converters.hugging_face.text_embedding import (
    MultilingualE5SmallEmbedding,
)
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.persistence import DensePersistence
from tests.back.converters.text_embedding_stub import with_fake_model


def _retriever(tmp_path):
    embedding = MultilingualE5SmallEmbedding()
    model = with_fake_model(embedding)
    chunks = {
        1: {
            index: Chunk(
                id=index,
                document_id=1,
                document_position=index,
                text=f"passage number {index}",
            )
            for index in range(3)
        }
    }
    persistence = DensePersistence(
        matrix_dirs={1: str(tmp_path / "matrix")}, embedding_model_id=1
    )
    retriever = DenseEmbeddingRetriever(
        embedding_model=embedding, similarity_metric="cosine", top_k=2
    )
    retriever.inject_infra(str(tmp_path), chunks, persistence)
    retriever.init_model()
    return retriever, model


def test_indexing_encodes_chunks_with_the_passage_role(tmp_path):
    _, model = _retriever(tmp_path)

    assert model.calls[0]["prompt"] == "passage: "
    assert model.calls[0]["sentences"] == [f"passage number {i}" for i in range(3)]
    assert np.load(tmp_path / "matrix" / "embeddings.npy").shape == (3, 8)


def test_dense_retriever_encodes_queries_with_the_query_role(tmp_path):
    retriever, model = _retriever(tmp_path)

    results = retriever.retrieve("what is passage one")
    scored = retriever.score_chunks([0, 2], "what is passage one")

    assert len(results) == 2
    assert [call["prompt"] for call in model.calls[1:]] == ["query: ", "query: "]
    assert {chunk_id for chunk_id, _ in scored} == {0, 2}


def test_the_retriever_records_the_converter_and_its_params(tmp_path):
    retriever, _ = _retriever(tmp_path)

    assert retriever.params["embedding_model"] == {
        "component": "MultilingualE5SmallEmbedding",
        "params": dict(sorted(MultilingualE5SmallEmbedding().params.items())),
    }
