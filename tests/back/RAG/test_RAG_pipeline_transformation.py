"""Tests for the optional query-transformation stage in the RAG pipeline.

Covers configuration parsing of the optional ``query_transformation`` key, the
round-robin merge of per-query retrieval results, prompt wiring, history
slicing, typed output and error wrapping. Uses mocks for retriever, prompt and
LLM; the transformer is a mock too.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGPipelineConfigError,
    RAGPipelineRuntimeError,
    RAGTransformationError,
)
from DashAI.back.models.RAG.RAG_pipeline import (
    ModelRef,
    PipelineStageTimings,
    RAGGenerationOutput,
    RAGPipeline,
    RAGPipelineConfig,
    merge_round_robin,
)
from DashAI.back.models.RAG.retrievers.trace_utils import chunk_ref

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _valid_kwargs(**overrides) -> dict:
    base = {
        "session_id": 1,
        "db": MagicMock(),
        "component_registry": MagicMock(),
        "env_RAG_path": "/tmp/rag",
        "documents": [10, 20],
        "prompt": {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en"},
        },
        "chunking_model": {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 200},
        },
        "retriever_model": {"component": "BM25Retriever", "params": {"top_k": 5}},
        "generation_model": {"component": "StubLLM", "params": {}},
    }
    base.update(overrides)
    return base


def _retriever_stub(chunks, name="MockRetriever"):
    """A ``(chunks, trace)`` tuple, the shape every retriever now returns."""
    return (chunks, {"name": name, "chunks": [chunk_ref(c) for c in chunks]})


def _make_pipeline(
    documents=None,
    retriever=None,
    prompt_model=None,
    llm_model=None,
    chunks=None,
    query_transformation=None,
) -> RAGPipeline:
    config = MagicMock(spec=RAGPipelineConfig)
    config.session_id = 1
    config.documents = [1, 2, 3]

    if documents is None:
        documents = {}
        for did in (1, 2, 3):
            doc = MagicMock()
            doc.file_name = f"doc{did}.txt"
            documents[did] = doc

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


def _transformer(queries=None) -> MagicMock:
    transformer = MagicMock()
    result = MagicMock()
    result.queries = ["q1", "q2"] if queries is None else queries
    transformer.transform.return_value = result
    return transformer


class _StubTransformer:
    """Tiny non-mock transformer returning a fixed query list."""

    def __init__(self, queries):
        self.queries = list(queries)
        self.calls = []

    def transform(self, message, history):
        self.calls.append({"message": message, "history": history})
        result = MagicMock()
        result.queries = list(self.queries)
        return result


class _SleepingTransformer:
    """Non-mock transformer whose transform() sleeps to make timing observable."""

    def __init__(self, sleep_seconds: float, queries=None):
        self.sleep_seconds = sleep_seconds
        self.queries = ["q1"] if queries is None else list(queries)

    def transform(self, message, history):
        time.sleep(self.sleep_seconds)
        result = MagicMock()
        result.queries = list(self.queries)
        return result


class _NoQueriesTransformer:
    """Transformer returning a result object that lacks ``.queries``."""

    def transform(self, message, history):
        return object()


# ===================================================================
# RAGPipelineConfig.from_kwargs — optional query_transformation
# ===================================================================


class TestConfigQueryTransformation:
    """Parsing of the optional ``query_transformation`` model ref."""

    def test_absent_key_is_none(self):
        config = RAGPipelineConfig.from_kwargs(**_valid_kwargs())
        assert config.query_transformation is None

    def test_explicit_none_is_none(self):
        config = RAGPipelineConfig.from_kwargs(
            **_valid_kwargs(query_transformation=None)
        )
        assert config.query_transformation is None

    def test_valid_ref_is_parsed(self):
        config = RAGPipelineConfig.from_kwargs(
            **_valid_kwargs(
                query_transformation={
                    "component": "LLMQueryRewriter",
                    "params": {"history_window": 2},
                }
            )
        )
        assert isinstance(config.query_transformation, ModelRef)
        assert config.query_transformation.component == "LLMQueryRewriter"
        assert config.query_transformation.params == {"history_window": 2}

    def test_not_a_dict_raises(self):
        with pytest.raises(RAGPipelineConfigError, match="must be a dict"):
            RAGPipelineConfig.from_kwargs(
                **_valid_kwargs(query_transformation="LLMQueryRewriter")
            )

    def test_missing_component_raises(self):
        with pytest.raises(RAGPipelineConfigError, match="Missing 'component'"):
            RAGPipelineConfig.from_kwargs(
                **_valid_kwargs(query_transformation={"params": {}})
            )

    def test_missing_params_raises(self):
        with pytest.raises(RAGPipelineConfigError, match="Missing 'params'"):
            RAGPipelineConfig.from_kwargs(
                **_valid_kwargs(query_transformation={"component": "LLMQueryRewriter"})
            )


# ===================================================================
# merge_round_robin
# ===================================================================


class TestMergeRoundRobin:
    """Round-robin interleave with de-duplication by (doc, position)."""

    def _chunk(self, doc: int, pos: int, text: str = "t") -> Chunk:
        return Chunk(id=None, document_id=doc, document_position=pos, text=text)

    def test_empty_input(self):
        assert merge_round_robin([]) == []

    def test_empty_lists_tolerated(self):
        assert merge_round_robin([[], []]) == []

    def test_single_list_unchanged(self):
        chunks = [self._chunk(1, 0), self._chunk(1, 1)]
        assert merge_round_robin([chunks]) == chunks

    def test_round_robin_interleave_and_dedupe(self):
        first = [self._chunk(1, 0), self._chunk(1, 1), self._chunk(2, 0)]
        second = [self._chunk(1, 1), self._chunk(2, 1), self._chunk(3, 0)]
        merged = merge_round_robin([first, second])
        keys = [(c.document_id, c.document_position) for c in merged]
        assert keys == [(1, 0), (1, 1), (2, 1), (2, 0), (3, 0)]

    def test_short_lists_are_skipped(self):
        first = [self._chunk(1, 0)]
        second = [self._chunk(2, 0), self._chunk(2, 1)]
        merged = merge_round_robin([first, second])
        assert [(c.document_id, c.document_position) for c in merged] == [
            (1, 0),
            (2, 0),
            (2, 1),
        ]


# ===================================================================
# multi_query_retrieval — the pipeline's only retrieval path
# ===================================================================


class TestUniformRetrievalPath:
    """Every list length goes through the same per-query retrieve + merge path."""

    def test_single_element_list_returns_retriever_output_unchanged(self):
        first = Chunk(id=None, document_id=1, document_position=0, text="a")
        second = Chunk(id=None, document_id=2, document_position=5, text="b")
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([first, second])
        pipeline = _make_pipeline(retriever=retriever)

        result, trace = pipeline.multi_query_retrieval(["only"])

        retriever.retrieve.assert_called_once_with("only")
        # A one-element list is a merge no-op: content and order are preserved.
        assert result == [first, second]
        assert [chunk.document_position for chunk in result] == [0, 5]
        # A single query still yields exactly one trace entry.
        assert trace == [
            {
                "query": "only",
                "retriever": {
                    "name": "MockRetriever",
                    "chunks": ["1_0", "2_5"],
                },
            }
        ]

    def test_multi_query_trace_carries_one_node_per_query(self):
        first = Chunk(id=None, document_id=1, document_position=0, text="a")
        second = Chunk(id=None, document_id=2, document_position=0, text="b")
        retriever = MagicMock()
        retriever.retrieve.side_effect = lambda query: _retriever_stub(
            [first] if query == "q1" else [second]
        )
        pipeline = _make_pipeline(retriever=retriever)

        result, trace = pipeline.multi_query_retrieval(["q1", "q2"])

        assert [c.document_position for c in result] == [0, 0]
        assert [entry["query"] for entry in trace] == ["q1", "q2"]
        assert [entry["retriever"]["chunks"] for entry in trace] == [["1_0"], ["2_0"]]


# ===================================================================
# RAGPipeline.generate — transformation disabled
# ===================================================================


class TestGenerateWithoutTransformation:
    """Backward-compatible behaviour when the stage is off."""

    def test_retriever_called_once_with_message(self):
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        prompt_model = MagicMock()
        prompt_model.format.return_value = "p"
        pipeline = _make_pipeline(retriever=retriever, prompt_model=prompt_model)
        result = pipeline.generate(({"role": "user", "content": "the message"},))
        retriever.retrieve.assert_called_once_with("the message")
        # The prompt's {queries} placeholder stays OPTIONAL: when no
        # transformation ran there are no transformed queries to send, so it is
        # ``None`` even though retrieval always runs over a one-element list.
        prompt_model.format.assert_called_once_with(
            input="the message", chunks="", queries=None
        )
        assert result.queries == ["the message"]

    def test_construction_without_transformation_kwarg(self):
        pipeline = _make_pipeline()
        assert pipeline.query_transformation is None

    def test_transformation_timing_is_exactly_zero(self):
        pipeline = _make_pipeline()
        result = pipeline.generate(({"role": "user", "content": "the message"},))
        assert isinstance(result.timings, PipelineStageTimings)
        assert result.timings.transformation_ms == 0.0


# ===================================================================
# RAGPipeline.generate — transformation enabled
# ===================================================================


class TestGenerateWithTransformation:
    """Transformation drives multi-query retrieval and prompt wiring."""

    def _retriever(self):
        first = [
            Chunk(id=None, document_id=1, document_position=0, text="a"),
            Chunk(id=None, document_id=1, document_position=1, text="b"),
            Chunk(id=None, document_id=2, document_position=0, text="c"),
        ]
        second = [
            Chunk(id=None, document_id=1, document_position=1, text="b"),
            Chunk(id=None, document_id=2, document_position=1, text="d"),
            Chunk(id=None, document_id=3, document_position=0, text="e"),
        ]
        retriever = MagicMock()
        retriever.retrieve.side_effect = lambda query: _retriever_stub(
            {"q1": first, "q2": second}[query]
        )
        return retriever

    def test_retriever_called_once_per_query(self):
        retriever = self._retriever()
        pipeline = _make_pipeline(
            retriever=retriever, query_transformation=_transformer(["q1", "q2"])
        )
        pipeline.generate(({"role": "user", "content": "msg"},))
        assert [call.args[0] for call in retriever.retrieve.call_args_list] == [
            "q1",
            "q2",
        ]

    def test_merged_chunks_are_round_robin_deduped(self):
        pipeline = _make_pipeline(
            retriever=self._retriever(),
            query_transformation=_transformer(["q1", "q2"]),
        )
        result = pipeline.generate(({"role": "user", "content": "msg"},))
        assert list(result.chunks) == ["1_0", "1_1", "2_1", "2_0", "3_0"]

    def test_prompt_receives_joined_queries(self):
        prompt_model = MagicMock()
        prompt_model.format.return_value = "p"
        pipeline = _make_pipeline(
            retriever=self._retriever(),
            prompt_model=prompt_model,
            query_transformation=_transformer(["q1", "q2"]),
        )
        pipeline.generate(({"role": "user", "content": "msg"},))
        assert prompt_model.format.call_args.kwargs["queries"] == "q1; q2"

    def test_output_carries_queries(self):
        pipeline = _make_pipeline(
            retriever=self._retriever(),
            query_transformation=_transformer(["q1", "q2"]),
        )
        result = pipeline.generate(({"role": "user", "content": "msg"},))
        assert isinstance(result, RAGGenerationOutput)
        assert result.queries == ["q1", "q2"]

    def test_single_rewrite_returns_one_element_query_list(self):
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        prompt_model = MagicMock()
        prompt_model.format.return_value = "p"
        pipeline = _make_pipeline(
            retriever=retriever,
            prompt_model=prompt_model,
            query_transformation=_transformer(["q1"]),
        )
        result = pipeline.generate(({"role": "user", "content": "raw message"},))
        retriever.retrieve.assert_called_once_with("q1")
        assert result.queries == ["q1"]
        assert prompt_model.format.call_args.kwargs["queries"] == "q1"

    def test_history_excludes_current_message(self):
        transformer = _transformer(["q1"])
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(retriever=retriever, query_transformation=transformer)
        input_data = (
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "answer"},
            {"role": "user", "content": "current"},
        )
        pipeline.generate(input_data)
        kwargs = transformer.transform.call_args.kwargs
        assert kwargs["message"] == "current"
        assert kwargs["history"] == [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "answer"},
        ]

    def test_transformation_error_is_wrapped(self):
        transformer = MagicMock()
        transformer.transform.side_effect = RAGTransformationError("boom")
        pipeline = _make_pipeline(
            retriever=MagicMock(), query_transformation=transformer
        )
        with pytest.raises(
            RAGPipelineRuntimeError, match="Query transformation failed"
        ):
            pipeline.generate(({"role": "user", "content": "msg"},))

    def test_unexpected_transformer_error_is_wrapped(self):
        """A non-RAG error from transform() surfaces as RAGPipelineRuntimeError."""
        transformer = MagicMock()
        transformer.transform.side_effect = RuntimeError("backend blew up")
        pipeline = _make_pipeline(
            retriever=MagicMock(), query_transformation=transformer
        )
        with pytest.raises(
            RAGPipelineRuntimeError, match="Query transformation failed"
        ):
            pipeline.generate(({"role": "user", "content": "msg"},))

    def test_transformer_result_without_queries_is_wrapped(self):
        """A result object without ``.queries`` surfaces as RAGPipelineRuntimeError."""
        pipeline = _make_pipeline(
            retriever=MagicMock(), query_transformation=_NoQueriesTransformer()
        )
        with pytest.raises(
            RAGPipelineRuntimeError,
            match="Query transformation returned no queries",
        ):
            pipeline.generate(({"role": "user", "content": "msg"},))

    def test_retrieval_error_propagates_as_runtime_error(self):
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("index gone")
        pipeline = _make_pipeline(
            retriever=retriever, query_transformation=_transformer(["q1"])
        )
        with pytest.raises(RAGPipelineRuntimeError, match="retrieval") as excinfo:
            pipeline.generate(({"role": "user", "content": "msg"},))
        # Single wrap: the retriever's own failure message must not get a
        # second "Failed during retrieval" prefix stacked on top of it.
        assert str(excinfo.value).startswith("Document retrieval failed")

    def test_retrieval_error_disabled_stage_single_wrap(self):
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("index gone")
        pipeline = _make_pipeline(retriever=retriever)
        with pytest.raises(RAGPipelineRuntimeError) as excinfo:
            pipeline.generate(({"role": "user", "content": "msg"},))
        assert str(excinfo.value).startswith("Document retrieval failed")

    def test_bare_list_retriever_fails_loudly(self):
        """A legacy retriever returning a bare list must not mis-unpack."""
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            Chunk(id=100, document_id=1, text="x", document_position=0)
        ]
        pipeline = _make_pipeline(retriever=retriever)
        with pytest.raises(RAGPipelineRuntimeError, match="Document retrieval failed"):
            pipeline.generate(({"role": "user", "content": "msg"},))

    def test_empty_transformation_queries_raise(self):
        retriever = MagicMock()
        pipeline = _make_pipeline(
            retriever=retriever, query_transformation=_transformer([])
        )
        with pytest.raises(
            RAGPipelineRuntimeError,
            match="Query transformation returned no queries",
        ):
            pipeline.generate(({"role": "user", "content": "msg"},))
        retriever.retrieve.assert_not_called()

    def test_stub_transformer_timing_and_result_flow_through(self):
        """A real (non-mock) transformer is timed and its query is retrieved."""
        transformer = _StubTransformer(["rewritten query"])
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(retriever=retriever, query_transformation=transformer)

        result = pipeline.generate(({"role": "user", "content": "raw"},))

        retriever.retrieve.assert_called_once_with("rewritten query")
        assert result.queries == ["rewritten query"]
        assert transformer.calls == [{"message": "raw", "history": []}]
        assert result.timings.transformation_ms >= 0.0
        assert result.timings.retrieval_ms >= 0.0
        assert result.timings.generation_ms >= 0.0
        assert result.timings.total_ms >= max(
            result.timings.transformation_ms,
            result.timings.retrieval_ms,
            result.timings.generation_ms,
        )

    def test_transformation_stage_is_actually_measured(self):
        """A 10 ms transform must show up as transformation_ms >= 5 ms (not 0.0)."""
        transformer = _SleepingTransformer(0.01)
        retriever = MagicMock()
        retriever.retrieve.return_value = _retriever_stub([])
        pipeline = _make_pipeline(retriever=retriever, query_transformation=transformer)

        timings = pipeline.generate(({"role": "user", "content": "raw"},)).timings

        assert timings.transformation_ms >= 5.0
        assert timings.total_ms >= 5.0
