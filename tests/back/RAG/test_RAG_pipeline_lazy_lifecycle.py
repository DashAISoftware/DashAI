"""Lifecycle tests for the per-stage lazy LLMs of ``RAGPipeline``.

Each RAG stage owns a differently configured LLM, but only one of them is
needed at a time. The pipeline must load a stage's model when the stage starts,
close it as soon as the stage ends, and keep the proxies reusable across turns.
These tests drive the pipeline with fakes whose LLM is a real
:class:`LazyLLM`, so construction and release are observed through the real
proxy rather than through mocks.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Dict, List
from unittest.mock import MagicMock

import pytest

from DashAI.back.models.lazy_llm import LazyLLM
from DashAI.back.models.RAG.exceptions import RAGPipelineRuntimeError
from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline, RAGPipelineConfig
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

# ---------------------------------------------------------------------------
# recording backend
# ---------------------------------------------------------------------------


class _RecordingBackend(TextToTextGenerationTaskModel):
    """Real model behind every lazy proxy, recording its lifecycle."""

    live = 0
    max_live = 0
    construction_count = 0
    close_count = 0
    events: List[str] = []

    def __init__(self, label: str, *, fail_generate: bool = False) -> None:
        self.label = label
        self.fail_generate = fail_generate
        self.closed = False
        type(self).construction_count += 1
        type(self).live += 1
        type(self).max_live = max(type(self).max_live, type(self).live)
        type(self).events.append(f"load:{label}")

    def generate(self, prompt):
        type(self).events.append(f"generate:{self.label}")
        if self.fail_generate:
            raise RuntimeError(f"{self.label} generation exploded")
        return [f"{self.label} answer"]

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        type(self).close_count += 1
        type(self).live -= 1
        type(self).events.append(f"close:{self.label}")


@pytest.fixture(autouse=True)
def _reset_recording() -> None:
    """Reset the shared lifecycle recording before every test."""
    _RecordingBackend.live = 0
    _RecordingBackend.max_live = 0
    _RecordingBackend.construction_count = 0
    _RecordingBackend.close_count = 0
    _RecordingBackend.events = []


# ---------------------------------------------------------------------------
# stage fakes owning a LazyLLM
# ---------------------------------------------------------------------------


class _ProxyTransformer:
    """Transformer whose model call goes through its lazy proxy."""

    def __init__(
        self,
        llm_model: LazyLLM,
        *,
        fail: bool = False,
        close_fails: bool = False,
        queries: List[str] | None = None,
    ) -> None:
        self.llm_model = llm_model
        self.fail = fail
        self.close_fails = close_fails
        self.queries = queries

    def transform(self, message: str, history: List[Dict[str, str]]):
        self.llm_model.generate([{"role": "user", "content": message}])
        if self.fail:
            raise RuntimeError("transformation exploded")
        queries = self.queries or [f"rewritten:{message}"]
        return SimpleNamespace(queries=list(queries))

    def close(self) -> None:
        self.llm_model.close()
        if self.close_fails:
            raise RuntimeError("transformer cleanup exploded")


class _ProxyRetriever:
    """Retriever whose evaluation call goes through its lazy proxy."""

    def __init__(self, llm_model: LazyLLM, *, fail: bool = False) -> None:
        self.llm_model = llm_model
        self.fail = fail

    def retrieve(self, query: str):
        self.llm_model.generate([{"role": "user", "content": query}])
        if self.fail:
            raise RuntimeError("retrieval exploded")
        return [], {"name": "ProxyRetriever", "chunks": []}

    def close(self) -> None:
        self.llm_model.close()


def _lazy(label: str, *, fail_generate: bool = False) -> LazyLLM:
    """Build a lazy proxy over a recording backend."""
    return LazyLLM(
        lambda: _RecordingBackend(label, fail_generate=fail_generate),
        label=label,
    )


def _pipeline(
    *,
    transform_llm: LazyLLM | None = None,
    retrieve_llm: LazyLLM | None = None,
    generation_llm: LazyLLM | None = None,
    transformer_fails: bool = False,
    transformer_close_fails: bool = False,
    retriever_fails: bool = False,
    generation_fails: bool = False,
    transformed_queries: List[str] | None = None,
) -> tuple[RAGPipeline, _ProxyTransformer, _ProxyRetriever]:
    """Build a pipeline with lazy-backed stage fakes."""
    transform_llm = transform_llm or _lazy("transform")
    retrieve_llm = retrieve_llm or _lazy("retrieval")
    generation_llm = generation_llm or _lazy(
        "generation", fail_generate=generation_fails
    )
    transformer = _ProxyTransformer(
        transform_llm,
        fail=transformer_fails,
        close_fails=transformer_close_fails,
        queries=transformed_queries,
    )
    retriever = _ProxyRetriever(retrieve_llm, fail=retriever_fails)

    config = MagicMock(spec=RAGPipelineConfig)
    config.session_id = 1
    config.documents = []
    prompt_model = MagicMock()
    prompt_model.format.return_value = "formatted prompt"

    pipeline = RAGPipeline(
        config=config,
        pipeline_id=1,
        chunking_model_id=2,
        documents={},
        chunks={},
        prompt_model=prompt_model,
        chunking_model=MagicMock(),
        retriever=retriever,
        llm_model=generation_llm,
        query_transformation=transformer,
    )
    return pipeline, transformer, retriever


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_stages_load_and_close_in_order_with_one_live_model() -> None:
    """Transform → retrieve → generate, each model closed right after its stage."""
    pipeline, _, _ = _pipeline()

    result = pipeline.generate(({"role": "user", "content": "hello"},))

    assert result.message == "generation answer"
    assert _RecordingBackend.events == [
        "load:transform",
        "generate:transform",
        "close:transform",
        "load:retrieval",
        "generate:retrieval",
        "close:retrieval",
        "load:generation",
        "generate:generation",
        "close:generation",
    ]
    # Every stage's model is closed before the next one is loaded.
    assert _RecordingBackend.events.index("close:transform") < (
        _RecordingBackend.events.index("load:retrieval")
    )
    assert _RecordingBackend.events.index("close:retrieval") < (
        _RecordingBackend.events.index("load:generation")
    )
    assert _RecordingBackend.max_live == 1
    assert _RecordingBackend.live == 0


def test_retrieval_llm_loads_once_for_all_queries_and_closes_after_stage() -> None:
    """The evaluation model serves every query, then is released once."""
    pipeline, _, _ = _pipeline(transformed_queries=["q1", "q2"])

    pipeline.generate(({"role": "user", "content": "hello"},))

    assert _RecordingBackend.events == [
        "load:transform",
        "generate:transform",
        "close:transform",
        "load:retrieval",
        "generate:retrieval",
        "generate:retrieval",
        "close:retrieval",
        "load:generation",
        "generate:generation",
        "close:generation",
    ]
    assert _RecordingBackend.events.count("load:retrieval") == 1
    assert _RecordingBackend.events.count("close:retrieval") == 1
    assert _RecordingBackend.max_live == 1
    assert _RecordingBackend.live == 0


def test_second_generate_call_reloads_each_proxy() -> None:
    """The same proxies survive ``generate`` and reload on the next turn."""
    transform_llm = _lazy("transform")
    retrieve_llm = _lazy("retrieval")
    generation_llm = _lazy("generation")
    pipeline, transformer, retriever = _pipeline(
        transform_llm=transform_llm,
        retrieve_llm=retrieve_llm,
        generation_llm=generation_llm,
    )

    pipeline.generate(({"role": "user", "content": "first"},))
    pipeline.generate(({"role": "user", "content": "second"},))

    # Three stages, two turns: each backend is constructed and closed twice.
    assert _RecordingBackend.construction_count == 6
    assert _RecordingBackend.close_count == 6
    assert _RecordingBackend.max_live == 1
    assert _RecordingBackend.live == 0

    # The proxies are the same objects and are idle between turns.
    assert pipeline.llm_model is generation_llm
    assert pipeline.retriever is retriever
    assert pipeline.query_transformation is transformer
    assert transform_llm.is_loaded is False
    assert retrieve_llm.is_loaded is False
    assert generation_llm.is_loaded is False


# ---------------------------------------------------------------------------
# failure paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("failing_stage", "expected_events"),
    [
        (
            "transformation",
            ["load:transform", "generate:transform", "close:transform"],
        ),
        (
            "retrieval",
            [
                "load:transform",
                "generate:transform",
                "close:transform",
                "load:retrieval",
                "generate:retrieval",
                "close:retrieval",
            ],
        ),
        (
            "generation",
            [
                "load:transform",
                "generate:transform",
                "close:transform",
                "load:retrieval",
                "generate:retrieval",
                "close:retrieval",
                "load:generation",
                "generate:generation",
                "close:generation",
            ],
        ),
    ],
)
def test_stage_failure_still_closes_its_model(
    failing_stage: str, expected_events: List[str]
) -> None:
    """A failed stage closes its model; the outer net leaves nothing loaded."""
    pipeline, _, _ = _pipeline(
        transformer_fails=failing_stage == "transformation",
        retriever_fails=failing_stage == "retrieval",
        generation_fails=failing_stage == "generation",
    )

    with pytest.raises(RAGPipelineRuntimeError):
        pipeline.generate(({"role": "user", "content": "hello"},))

    assert _RecordingBackend.events == expected_events
    assert _RecordingBackend.live == 0
    assert _RecordingBackend.max_live == 1


def test_release_swallows_cleanup_errors_and_missing_hooks() -> None:
    """Cleanup must never mask a stage failure."""
    calls: List[str] = []

    class _BrokenClose:
        def close(self) -> None:
            calls.append("close")
            raise RuntimeError("cleanup failed")

    RAGPipeline._release(_BrokenClose())
    RAGPipeline._release(object())
    RAGPipeline._release(None)

    assert calls == ["close"]


def test_stage_close_failure_cannot_replace_the_stage_error() -> None:
    """A raising teardown is logged, not surfaced over the stage failure."""
    pipeline, _, _ = _pipeline(transformer_fails=True, transformer_close_fails=True)

    with pytest.raises(RAGPipelineRuntimeError, match="transformation exploded"):
        pipeline.generate(({"role": "user", "content": "hello"},))

    # The model was still closed, so nothing remains resident.
    assert _RecordingBackend.live == 0


def test_total_timing_covers_every_stage_and_teardown() -> None:
    """``total_ms`` is taken after teardown, so it covers all stage work."""
    pipeline, _, _ = _pipeline()

    timings = pipeline.generate(({"role": "user", "content": "hello"},)).timings

    assert timings.total_ms >= (
        timings.transformation_ms + timings.retrieval_ms + timings.generation_ms
    )
    assert timings.transformation_ms > 0.0
    assert timings.retrieval_ms > 0.0
    assert timings.generation_ms > 0.0


# ---------------------------------------------------------------------------
# composite close isolation
# ---------------------------------------------------------------------------


class _CloseTrackingRetriever(BaseRetriever):
    """Leaf retriever that records its close calls."""

    def __init__(self, name: str, *, fail_close: bool = False) -> None:
        super().__init__()
        self.name = name
        self.fail_close = fail_close
        self.close_calls = 0

    def retrieve(self, query, **kwargs):
        return [], {"name": self.name, "chunks": []}

    def score_chunks(self, chunk_ids, query):
        return []

    @property
    def retrieval_top_k(self) -> int:
        return 0

    def close(self) -> None:
        self.close_calls += 1
        if self.fail_close:
            raise RuntimeError(f"{self.name} close exploded")


class _TestComposite(CompositeRetriever):
    """Minimal concrete composite used only for the close-isolation test."""

    def retrieve(self, query, **kwargs):
        return [], {"name": type(self).__name__, "chunks": []}

    def score_chunks(self, chunk_ids, query):
        return []

    @property
    def retrieval_top_k(self) -> int:
        return 0


def test_composite_close_isolates_a_failing_child() -> None:
    """One child's close failure must not skip the remaining children."""
    failing = _CloseTrackingRetriever("failing", fail_close=True)
    healthy = _CloseTrackingRetriever("healthy")
    composite = _TestComposite(children=[failing, healthy])

    composite.close()

    assert failing.close_calls == 1
    assert healthy.close_calls == 1


# ---------------------------------------------------------------------------
# direct lifecycle probe
# ---------------------------------------------------------------------------


def test_lifecycle_probe_prints_construction_and_close_order() -> None:
    """Print the observed order and prove the peak is one live backend.

    Run this test with ``-s`` to see the probe output; it is also asserted so a
    captured run still fails if the order regresses.
    """
    pipeline, _, _ = _pipeline()

    pipeline.generate(({"role": "user", "content": "probe"},))

    import sys

    for event in _RecordingBackend.events:
        print(f"[probe] {event}", file=sys.stdout)
    print(
        f"[probe] max_live={_RecordingBackend.max_live} "
        f"live_after_turn={_RecordingBackend.live}",
        file=sys.stdout,
    )

    assert _RecordingBackend.events == [
        "load:transform",
        "generate:transform",
        "close:transform",
        "load:retrieval",
        "generate:retrieval",
        "close:retrieval",
        "load:generation",
        "generate:generation",
        "close:generation",
    ]
    assert _RecordingBackend.max_live == 1
    assert _RecordingBackend.live == 0
