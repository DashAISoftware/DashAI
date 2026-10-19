"""Unit tests for RAGPipeline live stage-progress reporting.

The pipeline accepts an optional ``progress_callback`` that receives one small
JSON-shaped payload per stage. These tests construct ``RAGPipeline`` directly
with mock dependencies (the pattern of ``test_RAG_pipeline_unit.py``) and assert
the exact event sequence the frontend contract requires:

- the query-transformation stage is reported only when it is enabled;
- the retrieval stage carries the resolved queries as a plain list of strings;
- the generation stage is reported last.

The payload literals are asserted verbatim on purpose: the tests pin the wire
contract the frontend consumes, independently of the backend constants.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline, RAGPipelineConfig
from DashAI.back.models.RAG.retrievers.trace_utils import chunk_ref

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _retriever_stub(chunks):
    """A ``(chunks, trace)`` tuple, the shape every retriever now returns."""
    return (chunks, {"name": "MockRetriever", "chunks": [chunk_ref(c) for c in chunks]})


def _transformer(queries):
    """A transformer stub whose ``transform`` returns ``queries``."""
    transformer = MagicMock()
    result = MagicMock()
    result.queries = list(queries)
    transformer.transform.return_value = result
    return transformer


def _make_pipeline(
    documents=None,
    retriever=None,
    prompt_model=None,
    llm_model=None,
    chunks=None,
    query_transformation=None,
) -> RAGPipeline:
    """Build a RAGPipeline with mock dependencies for generate() tests."""
    config = MagicMock(spec=RAGPipelineConfig)
    config.session_id = 1
    config.documents = [1, 2]

    if documents is None:
        doc1 = MagicMock()
        doc1.file_name = "doc1.txt"
        doc2 = MagicMock()
        doc2.file_name = "doc2.txt"
        documents = {1: doc1, 2: doc2}

    if retriever is None:
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])

    if prompt_model is None:
        prompt_model = MagicMock()
        prompt_model.format.return_value = "formatted prompt"

    if llm_model is None:
        llm_model = MagicMock()
        llm_model.generate.return_value = ["stub answer"]

    if chunks is None:
        chunks = {}

    return RAGPipeline(
        config=config,
        pipeline_id=100,
        chunking_model_id=200,
        documents=documents,
        chunks=chunks,
        prompt_model=prompt_model,
        chunking_model=MagicMock(),
        retriever=retriever,
        llm_model=llm_model,
        query_transformation=query_transformation,
    )


# ===================================================================
# transformation disabled
# ===================================================================


class TestProgressWithoutTransformation:
    def test_emits_retrieving_then_generating(self):
        """No transformation stage → exactly retrieving then generating."""
        events = []
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(retriever=retriever)

        pipeline.generate(
            ({"role": "user", "content": "the message"},),
            progress_callback=events.append,
        )

        assert events == [
            {"stage": "retrieving", "queries": ["the message"]},
            {"stage": "generating"},
        ]

    def test_never_emits_transforming(self):
        """A disabled transformation stage emits no transforming event."""
        events = []
        pipeline = _make_pipeline()

        pipeline.generate(({"role": "user", "content": "hello"},), events.append)

        assert all(event["stage"] != "transforming" for event in events)


# ===================================================================
# transformation enabled
# ===================================================================


class TestProgressWithTransformation:
    def test_emits_transforming_retrieving_generating(self):
        """Enabled transformation → transforming, retrieving, generating."""
        events = []
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(
            retriever=retriever,
            query_transformation=_transformer(["q1", "q2"]),
        )

        pipeline.generate(
            ({"role": "user", "content": "msg"},),
            progress_callback=events.append,
        )

        assert events == [
            {"stage": "transforming"},
            {"stage": "retrieving", "queries": ["q1", "q2"]},
            {"stage": "generating"},
        ]

    def test_transforming_recorded_before_retrieve(self):
        """The transforming event precedes the first retriever call."""
        order = []
        retriever = MagicMock()
        retriever.retrieve.side_effect = lambda query: (
            order.append("retrieve") or _retriever_stub([])
        )
        pipeline = _make_pipeline(
            retriever=retriever,
            query_transformation=_transformer(["only"]),
        )

        pipeline.generate(
            ({"role": "user", "content": "msg"},),
            progress_callback=lambda event: order.append(event["stage"]),
        )

        assert order[0] == "transforming"
        assert order.index("retrieving") < order.index("retrieve")


# ===================================================================
# callback is optional
# ===================================================================


class TestProgressOptionalCallback:
    def test_generate_without_callback_still_works(self):
        """Omitting the callback leaves the existing behaviour unchanged."""
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(retriever=retriever)

        result = pipeline.generate(({"role": "user", "content": "hello"},))

        assert result.message == "stub answer"
        assert result.queries == ["hello"]


# ===================================================================
# queries payload
# ===================================================================


class TestProgressQueriesPayload:
    def test_queries_payload_matches_retrieved_queries(self):
        """The retrieval payload lists exactly the queries actually retrieved."""
        events = []
        retriever = MagicMock()
        retriever.retrieve.side_effect = lambda query: _retriever_stub([])
        pipeline = _make_pipeline(
            retriever=retriever,
            query_transformation=_transformer(["alpha", "beta"]),
        )

        pipeline.generate(
            ({"role": "user", "content": "msg"},),
            progress_callback=events.append,
        )

        retrieval_event = events[1]
        assert retrieval_event["stage"] == "retrieving"
        assert retrieval_event["queries"] == [
            call.args[0] for call in retriever.retrieve.call_args_list
        ]
        assert all(isinstance(query, str) for query in retrieval_event["queries"])

    def test_queries_payload_is_plain_list(self):
        """The queries payload is a list (JSON-native), never a tuple/set."""
        events = []
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub(
            [Chunk(id=1, document_id=1, document_position=0, text="t")]
        )
        pipeline = _make_pipeline(retriever=retriever)

        pipeline.generate(
            ({"role": "user", "content": "hello"},),
            progress_callback=events.append,
        )

        assert type(events[0]["queries"]) is list
