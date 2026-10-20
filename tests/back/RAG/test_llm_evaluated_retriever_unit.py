"""Unit tests for the LLM-evaluated composite retrievers.

Instances are constructed directly (no factory) with a scripted fake LLM, fake
children and a recording prompt. These tests pin the round semantics, the budget
and progress rules, the strict failure policy, the trace shape and the parser's
tolerance/strictness.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Dict, List, Optional, Tuple

import pytest

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions.retriever import RAGRetrieverEvaluationError
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    CHILDREN_KEY,
    SUFFICIENT_KEY,
    TOP_K_KEY,
    RetrievalVerdict,
    parse_evaluation_arguments,
    parse_evaluation_output,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_depth_retriever import (
    LLMEvaluatedDepthRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_ensemble_retriever import (  # noqa: E501
    LLMEvaluatedEnsembleRetriever,
)
from DashAI.back.models.RAG.retrievers.exceptions import CompositeValidationError
from DashAI.back.models.RAG.retrievers.trace_utils import retriever_trace
from DashAI.back.models.text_to_text_generation_model import (
    FunctionCallResult,
    TextToTextGenerationTaskModel,
)

# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------


def _chunks(count: int, document_id: int = 1) -> List[Chunk]:
    """Build ``count`` persisted-looking chunks for one document."""
    return [
        Chunk(
            id=document_id * 100 + position,
            document_id=document_id,
            document_position=position,
            text=f"chunk-{document_id}-{position}",
        )
        for position in range(count)
    ]


class _FakeChild(BaseRetriever):
    """Deterministic child retriever honouring a per-call ``top_k`` hint."""

    def __init__(
        self,
        chunks: List[Chunk],
        top_k: int,
        default_size: Optional[int] = None,
    ) -> None:
        """Store the corpus, the configured top-k and the no-override size."""
        super().__init__()
        self._corpus = chunks
        self._top_k = top_k
        self._default_size = default_size
        self.retrieve_calls: List[Optional[int]] = []

    def retrieve(
        self, query: str, top_k: Optional[int] = None, **kwargs: Any
    ) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Return the corpus prefix for the effective size."""
        self.retrieve_calls.append(top_k)
        effective = top_k if top_k is not None else self._default_size
        chunks = (
            list(self._corpus) if effective is None else list(self._corpus[:effective])
        )
        return chunks, retriever_trace(self, chunks)

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Return a constant distance per requested chunk."""
        return [(cid, 0.5) for cid in chunk_ids]

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k."""
        return self._top_k


class _ScriptedLLM(TextToTextGenerationTaskModel):
    """Fake LLM returning queued canned outputs and recording its prompts.

    Each queued entry is either a raw string (returned as a one-element list) or
    a list returned verbatim, so malformed-output cases can be scripted too.
    """

    def __init__(self, outputs: List[Any]) -> None:
        """Store the queue of outputs to return."""
        self._outputs = list(outputs)
        self.calls: List[Any] = []
        self.function_call_calls: List[Dict[str, Any]] = []

    def generate(self, input: Any) -> List[Any]:
        """Pop and return the next scripted output."""
        self.calls.append(input)
        if not self._outputs:
            raise AssertionError("No scripted LLM output left.")
        entry = self._outputs.pop(0)
        if isinstance(entry, str):
            return [entry]
        return entry

    def generate_function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
    ) -> FunctionCallResult:
        """Record the call; the text route must never reach this method."""
        self.function_call_calls.append({"messages": messages, "functions": functions})
        raise AssertionError(
            "generate_function_call() must not be called on the text path"
        )


class _FunctionCallingScriptedLLM(TextToTextGenerationTaskModel):
    """Fake function-calling LLM returning queued results or a configured error.

    ``generate`` deliberately fails: any accidental fall-through to the text
    route surfaces as a test failure instead of a silently tolerated call.
    """

    SUPPORTS_FUNCTION_CALLING = True

    def __init__(
        self,
        results: Optional[List[Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Store the queue of results and an optional error to raise."""
        self._results = list(results or [])
        self._error = error
        self.generate_calls: List[Any] = []
        self.fc_calls: List[Dict[str, Any]] = []

    def generate(self, input: Any) -> List[Any]:
        """Fail: the function-calling route must be selected instead."""
        self.generate_calls.append(input)
        raise AssertionError("generate() must not be called on the FC path")

    def generate_function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
    ) -> FunctionCallResult:
        """Record the call and return the next scripted result or error."""
        self.fc_calls.append({"messages": messages, "functions": functions})
        if self._error is not None:
            raise self._error
        if not self._results:
            raise AssertionError("No scripted function call left.")
        return self._results.pop(0)


class _RecordingPrompt:
    """Fake sufficiency prompt recording its rendering arguments."""

    def __init__(self) -> None:
        """Initialise an empty call log."""
        self.calls: List[Dict[str, Any]] = []

    def format(
        self,
        input: str,
        chunks: str,
        children_catalog: Optional[str] = None,
        pool_size: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Record the arguments and return a stable placeholder string."""
        self.calls.append(
            {
                "input": input,
                "chunks": chunks,
                "children_catalog": children_catalog,
                "pool_size": pool_size,
            }
        )
        return f"EVAL pool={pool_size} catalog={children_catalog}"


def _depth(
    child: _FakeChild,
    llm: _ScriptedLLM,
    prompt: _RecordingPrompt,
    max_iters: int,
    max_chunks: int,
) -> LLMEvaluatedDepthRetriever:
    """Construct a depth retriever directly."""
    return LLMEvaluatedDepthRetriever(
        children=[child],
        max_iters=max_iters,
        max_chunks=max_chunks,
        prompt=prompt,
        llm_model=llm,
    )


def _ensemble(
    children: List[_FakeChild],
    llm: _ScriptedLLM,
    prompt: _RecordingPrompt,
    max_iters: int,
    max_chunks: int,
) -> LLMEvaluatedEnsembleRetriever:
    """Construct an ensemble retriever directly."""
    return LLMEvaluatedEnsembleRetriever(
        children=children,
        max_iters=max_iters,
        max_chunks=max_chunks,
        prompt=prompt,
        llm_model=llm,
    )


# ---------------------------------------------------------------------------
# Retriever I — depth
# ---------------------------------------------------------------------------


def test_depth_sufficient_after_first_round():
    """A sufficient verdict in round 1 stops after one delegation and one call."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=3)
    llm = _ScriptedLLM(['{"sufficient": true}'])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=3, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 3
    assert child.retrieve_calls == [None]
    assert len(llm.calls) == 1
    assert retriever.retrieval_top_k == 10
    assert trace["name"] == "LLMEvaluatedDepthRetriever"
    assert len(trace["children"]) == 1
    assert len(trace["rounds"]) == 1
    assert trace["rounds"][0]["verdict"] is True
    assert trace["rounds"][0]["requested_top_k"] is None
    assert trace["rounds"][0]["returned"] == 3


def test_depth_insufficient_chain_honours_top_k_and_stops_at_max_iters():
    """Each insufficient verdict's top_k drives the next delegation."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=2)
    llm = _ScriptedLLM(
        [
            '{"sufficient": false, "top_k": 4}',
            '{"sufficient": false, "top_k": 6}',
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=3, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert [c.document_position for c in pool] == [0, 1, 2, 3, 4, 5]
    assert child.retrieve_calls == [None, 4, 6]
    assert len(llm.calls) == 2
    assert [entry["verdict"] for entry in trace["rounds"]] == [False, False, None]
    assert len(trace["rounds"]) == 3
    assert len(pool) <= retriever.retrieval_top_k


def test_depth_progress_guarantee_bumps_zero_progress_request():
    """A request that cannot add a chunk is raised to the smallest useful size."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=2)
    llm = _ScriptedLLM(['{"sufficient": false, "top_k": 1}'])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert child.retrieve_calls == [None, 3]
    assert len(pool) == 3
    assert trace["rounds"][1]["requested_top_k"] == 3


def test_depth_pool_dedup_and_cap():
    """The pool never exceeds max_chunks and drops duplicate chunks."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=10)
    llm = _ScriptedLLM([])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=1, max_chunks=3)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 3
    assert len({(c.document_id, c.document_position) for c in pool}) == 3


def test_depth_insufficient_without_top_k_raises():
    """An insufficient verdict lacking top_k fails loudly."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _ScriptedLLM(['{"sufficient": false}'])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=10)

    with pytest.raises(RAGRetrieverEvaluationError, match="top_k"):
        retriever.retrieve("q")


def test_depth_requires_exactly_one_child():
    """Construction rejects anything but exactly one child."""
    llm = _ScriptedLLM([])
    prompt = _RecordingPrompt()
    with pytest.raises(CompositeValidationError, match="exactly one"):
        LLMEvaluatedDepthRetriever(
            children=[_FakeChild(_chunks(3), top_k=3), _FakeChild(_chunks(3), top_k=3)],
            max_iters=2,
            max_chunks=5,
            prompt=prompt,
            llm_model=llm,
        )


def test_depth_prompt_is_blind_to_child_identity():
    """The depth prompt never receives a children catalog."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _ScriptedLLM(['{"sufficient": true}'])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=5)

    retriever.retrieve("q")

    assert prompt.calls[0]["children_catalog"] is None
    assert prompt.calls[0]["pool_size"] == 2


# ---------------------------------------------------------------------------
# Function calling — depth
# ---------------------------------------------------------------------------


def test_depth_function_calling_sufficient_stops_after_one_delegation():
    """A sufficient FC verdict stops after one delegation using the schema."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=3)
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("evaluate_retrieval_sufficiency", {"sufficient": True})]
    )
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=3, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 3
    assert child.retrieve_calls == [None]
    assert llm.generate_calls == []
    assert len(llm.fc_calls) == 1
    assert llm.fc_calls[0]["functions"] == [
        {
            "name": "evaluate_retrieval_sufficiency",
            "description": LLMEvaluatedDepthRetriever.FUNCTION_DESCRIPTION,
            "parameters": LLMEvaluatedDepthRetriever.FUNCTION_PARAMETERS,
        }
    ]
    assert llm.fc_calls[0]["messages"] == [
        {"role": "user", "content": "EVAL pool=3 catalog=None"}
    ]
    parameters = llm.fc_calls[0]["functions"][0]["parameters"]
    assert parameters["required"] == [SUFFICIENT_KEY]
    assert parameters["properties"][SUFFICIENT_KEY]["type"] == "boolean"
    assert parameters["properties"][TOP_K_KEY]["type"] == "integer"
    assert parameters["properties"][TOP_K_KEY]["minimum"] == 1
    assert trace["rounds"][0]["verdict"] is True


def test_depth_function_calling_insufficient_drives_next_top_k():
    """An insufficient FC verdict's top_k drives the next delegation."""
    child = _FakeChild(_chunks(10), top_k=10, default_size=2)
    llm = _FunctionCallingScriptedLLM(
        [
            FunctionCallResult(
                "evaluate_retrieval_sufficiency",
                {"sufficient": False, "top_k": 4},
            ),
            FunctionCallResult(
                "evaluate_retrieval_sufficiency",
                {"sufficient": False, "top_k": 6},
            ),
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=3, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert child.retrieve_calls == [None, 4, 6]
    assert len(pool) == 6
    assert len(llm.fc_calls) == 2
    assert llm.generate_calls == []
    assert [entry["verdict"] for entry in trace["rounds"]] == [False, False, None]


def test_depth_function_calling_resolves_json_string_arguments():
    """FC arguments emitted as a JSON-encoded string are resolved."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("evaluate_retrieval_sufficiency", '{"sufficient": true}')]
    )
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=5)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 2
    assert trace["rounds"][0]["verdict"] is True
    assert llm.generate_calls == []


# ---------------------------------------------------------------------------
# Retriever II — ensemble
# ---------------------------------------------------------------------------


def test_ensemble_planning_chooses_children_and_catalog_rendered():
    """The planning call selects children from a rendered catalog."""
    child0 = _FakeChild(_chunks(5), top_k=2)
    child1 = _FakeChild(_chunks(5), top_k=3)
    llm = _ScriptedLLM(
        [
            '{"sufficient": false, "children": [1]}',
            '{"sufficient": true}',
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _ensemble([child0, child1], llm, prompt, max_iters=2, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 3
    assert child0.retrieve_calls == []
    assert child1.retrieve_calls == [3]
    assert len(llm.calls) == 2
    assert trace["rounds"][0]["verdict"] is True
    assert trace["rounds"][0]["calls"] == [
        {"name": "_FakeChild", "requested_top_k": 3, "returned": 3}
    ]
    assert trace["children"][0]["name"] == "_FakeChild"
    # The catalog is rendered for the ensemble and names both children.
    catalog = prompt.calls[0]["children_catalog"]
    assert "[0]" in catalog
    assert "[1]" in catalog
    assert prompt.calls[0]["pool_size"] == 0


def test_ensemble_reconsult_escalates_top_k():
    """A child chosen in successive rounds is delegated an escalated size."""
    child0 = _FakeChild(_chunks(10), top_k=2)
    llm = _ScriptedLLM(
        [
            '{"sufficient": false, "children": [0]}',
            '{"sufficient": false, "children": [0]}',
            '{"sufficient": false, "children": [0]}',
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _ensemble([child0, _FakeChild(_chunks(3), top_k=3)], llm, prompt, 3, 10)

    pool, trace = retriever.retrieve("q")

    assert child0.retrieve_calls == [2, 4, 6]
    assert len(pool) == 6
    assert [entry["verdict"] for entry in trace["rounds"]] == [False, False, None]
    assert trace["rounds"][0]["calls"][0]["requested_top_k"] == 2
    assert trace["rounds"][1]["calls"][0]["requested_top_k"] == 4


@pytest.mark.parametrize(
    "planning",
    [
        '{"sufficient": false, "children": [5]}',
        '{"sufficient": false, "children": []}',
        '{"sufficient": false, "children": [-1]}',
        '{"sufficient": true}',
    ],
)
def test_ensemble_rejects_bad_planning_verdict(planning: str):
    """Invalid planning verdicts fail loudly."""
    children = [_FakeChild(_chunks(3), top_k=2), _FakeChild(_chunks(3), top_k=2)]
    llm = _ScriptedLLM([planning])
    prompt = _RecordingPrompt()
    retriever = _ensemble(children, llm, prompt, max_iters=2, max_chunks=10)

    with pytest.raises(RAGRetrieverEvaluationError):
        retriever.retrieve("q")


def test_ensemble_pool_never_exceeds_max_chunks():
    """The ensemble pool is capped at max_chunks."""
    child0 = _FakeChild(_chunks(10), top_k=10)
    child1 = _FakeChild(_chunks(10), top_k=10)
    llm = _ScriptedLLM(
        [
            '{"sufficient": false, "children": [0, 1]}',
            '{"sufficient": true}',
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _ensemble([child0, child1], llm, prompt, max_iters=2, max_chunks=4)

    pool, _ = retriever.retrieve("q")

    assert len(pool) == 4


def test_ensemble_function_calling_planning_selects_child():
    """An FC planning verdict selects child 1 and the schema exposes children."""
    child0 = _FakeChild(_chunks(5), top_k=2)
    child1 = _FakeChild(_chunks(5), top_k=3)
    llm = _FunctionCallingScriptedLLM(
        [
            FunctionCallResult(
                "evaluate_retrieval_sufficiency",
                {"sufficient": False, "children": [1]},
            ),
            FunctionCallResult("evaluate_retrieval_sufficiency", {"sufficient": True}),
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _ensemble([child0, child1], llm, prompt, max_iters=2, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert len(pool) == 3
    assert child0.retrieve_calls == []
    assert child1.retrieve_calls == [3]
    assert llm.generate_calls == []
    assert len(llm.fc_calls) == 2
    planning_spec = llm.fc_calls[0]["functions"][0]
    assert planning_spec["name"] == "evaluate_retrieval_sufficiency"
    assert planning_spec["description"] == (
        LLMEvaluatedEnsembleRetriever.FUNCTION_DESCRIPTION
    )
    parameters = planning_spec["parameters"]
    assert CHILDREN_KEY in parameters["properties"]
    children_schema = parameters["properties"][CHILDREN_KEY]
    assert children_schema["type"] == "array"
    assert children_schema["items"] == {"type": "integer", "minimum": 0}
    assert children_schema["minItems"] == 1
    assert parameters["required"] == [SUFFICIENT_KEY]
    assert parameters["properties"][SUFFICIENT_KEY]["type"] == "boolean"
    assert trace["rounds"][0]["verdict"] is True


def test_ensemble_function_calling_post_round_insufficient_selects_new_children():
    """A post-round insufficient FC verdict selects the next round's children."""
    child0 = _FakeChild(_chunks(10, document_id=1), top_k=2)
    child1 = _FakeChild(_chunks(10, document_id=2), top_k=3)
    llm = _FunctionCallingScriptedLLM(
        [
            FunctionCallResult(
                "evaluate_retrieval_sufficiency",
                {"sufficient": False, "children": [0]},
            ),
            FunctionCallResult(
                "evaluate_retrieval_sufficiency",
                {"sufficient": False, "children": [1]},
            ),
            FunctionCallResult("evaluate_retrieval_sufficiency", {"sufficient": True}),
        ]
    )
    prompt = _RecordingPrompt()
    retriever = _ensemble([child0, child1], llm, prompt, max_iters=3, max_chunks=10)

    pool, trace = retriever.retrieve("q")

    assert child0.retrieve_calls == [2]
    assert child1.retrieve_calls == [3]
    assert len(pool) == 5
    assert llm.generate_calls == []
    assert len(llm.fc_calls) == 3
    assert [entry["verdict"] for entry in trace["rounds"]] == [False, True]


# ---------------------------------------------------------------------------
# Common behaviour
# ---------------------------------------------------------------------------


def test_both_retrievers_trace_has_children_and_rounds():
    """Both retrievers expose children and rounds in their trace node."""
    llm = _ScriptedLLM(['{"sufficient": true}'])
    prompt = _RecordingPrompt()
    depth = _depth(_FakeChild(_chunks(5), top_k=5, default_size=2), llm, prompt, 2, 5)
    _, depth_trace = depth.retrieve("q")
    assert "children" in depth_trace
    assert "rounds" in depth_trace

    llm2 = _ScriptedLLM(
        ['{"sufficient": false, "children": [0]}', '{"sufficient": true}']
    )
    prompt2 = _RecordingPrompt()
    ensemble = _ensemble(
        [_FakeChild(_chunks(5), top_k=2), _FakeChild(_chunks(5), top_k=2)],
        llm2,
        prompt2,
        2,
        5,
    )
    _, ensemble_trace = ensemble.retrieve("q")
    assert "children" in ensemble_trace
    assert "rounds" in ensemble_trace
    assert ensemble_trace["name"] == "LLMEvaluatedEnsembleRetriever"


@pytest.mark.parametrize("bad", ["not json at all", '{"sufficient": "yes"}'])
def test_malformed_model_output_raises(bad: str):
    """A non-JSON or wrong-typed verdict fails loudly."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _ScriptedLLM([bad])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=10)

    with pytest.raises(RAGRetrieverEvaluationError):
        retriever.retrieve("q")


@pytest.mark.parametrize("bad_output", [[], [123]])
def test_non_string_or_empty_model_output_raises(bad_output: List[Any]):
    """An empty list or non-string first element fails loudly."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _ScriptedLLM([bad_output])
    prompt = _RecordingPrompt()
    retriever = _depth(child, llm, prompt, max_iters=2, max_chunks=10)

    with pytest.raises(RAGRetrieverEvaluationError):
        retriever.retrieve("q")


# ---------------------------------------------------------------------------
# Function calling — validation and route selection
# ---------------------------------------------------------------------------


def _fc_depth(
    llm: _FunctionCallingScriptedLLM,
) -> LLMEvaluatedDepthRetriever:
    """Construct a depth retriever wired to a function-calling fake."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    return _depth(child, llm, _RecordingPrompt(), max_iters=2, max_chunks=10)


def test_function_calling_wrong_name_raises():
    """A call naming an unexpected function fails loudly with both names."""
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("some_other_function", {"sufficient": True})]
    )

    with pytest.raises(RAGRetrieverEvaluationError) as excinfo:
        _fc_depth(llm).retrieve("q")
    message = str(excinfo.value)
    assert "some_other_function" in message
    assert "evaluate_retrieval_sufficiency" in message


def test_function_calling_empty_name_raises():
    """A call with no function name fails loudly."""
    llm = _FunctionCallingScriptedLLM([FunctionCallResult("", {"sufficient": True})])

    with pytest.raises(RAGRetrieverEvaluationError, match="name"):
        _fc_depth(llm).retrieve("q")


@pytest.mark.parametrize("result", [None, {}])
def test_function_calling_unexpected_result_type_raises(result: Any):
    """A non-FunctionCallResult return value fails loudly."""
    llm = _FunctionCallingScriptedLLM([result])

    with pytest.raises(RAGRetrieverEvaluationError):
        _fc_depth(llm).retrieve("q")


def test_function_calling_invalid_arguments_type_raises():
    """A list arguments payload (neither dict nor JSON string) fails loudly."""
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("evaluate_retrieval_sufficiency", [1, 2])]
    )

    with pytest.raises(RAGRetrieverEvaluationError):
        _fc_depth(llm).retrieve("q")


@pytest.mark.parametrize(
    "arguments",
    [
        {"sufficient": "yes"},
        {"sufficient": False, "top_k": 0},
        {"sufficient": False, "children": [1.5]},
        None,
    ],
)
def test_function_calling_invalid_dict_payload_raises(arguments: Any):
    """Invalid decoded arguments payloads fail loudly."""
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("evaluate_retrieval_sufficiency", arguments)]
    )

    with pytest.raises(RAGRetrieverEvaluationError):
        _fc_depth(llm).retrieve("q")


def test_function_calling_value_error_is_wrapped():
    """A backend ValueError is wrapped mentioning function-calling failure."""
    llm = _FunctionCallingScriptedLLM(error=ValueError("bad backend value"))

    with pytest.raises(
        RAGRetrieverEvaluationError,
        match="Function calling failed",
    ) as excinfo:
        _fc_depth(llm).retrieve("q")
    assert "bad backend value" in str(excinfo.value)


def test_function_calling_type_error_propagates():
    """An unexpected TypeError from a drifted backend is not swallowed."""
    llm = _FunctionCallingScriptedLLM(error=TypeError("unexpected shape"))

    with pytest.raises(TypeError, match="unexpected shape"):
        _fc_depth(llm).retrieve("q")


def test_function_calling_missing_spec_is_actionable():
    """A subclass without a declared function spec fails with guidance."""

    class _NoSpecDepthRetriever(LLMEvaluatedDepthRetriever):
        EXPECTED_FUNCTION = ""
        FUNCTION_DESCRIPTION = ""
        FUNCTION_PARAMETERS: Dict[str, Any] = {}

    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _FunctionCallingScriptedLLM(
        [FunctionCallResult("evaluate_retrieval_sufficiency", {"sufficient": True})]
    )
    retriever = _NoSpecDepthRetriever(
        children=[child],
        max_iters=2,
        max_chunks=10,
        prompt=_RecordingPrompt(),
        llm_model=llm,
    )

    with pytest.raises(
        RAGRetrieverEvaluationError,
        match="does not declare a function spec",
    ):
        retriever.retrieve("q")


def test_function_calling_backend_failure_is_wrapped():
    """A backend RuntimeError is wrapped mentioning function-calling failure."""
    llm = _FunctionCallingScriptedLLM(error=RuntimeError("backend exploded"))

    with pytest.raises(
        RAGRetrieverEvaluationError,
        match="Function calling failed",
    ) as excinfo:
        _fc_depth(llm).retrieve("q")
    assert "backend exploded" in str(excinfo.value)


def test_function_calling_not_implemented_is_actionable():
    """A model claiming support without an implementation fails actionably."""
    llm = _FunctionCallingScriptedLLM(error=NotImplementedError("not here"))

    with pytest.raises(
        RAGRetrieverEvaluationError,
        match="reports function calling support",
    ):
        _fc_depth(llm).retrieve("q")


def test_text_route_uses_generate_and_never_function_calling():
    """A non-FC model keeps using generate() and never generate_function_call()."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    llm = _ScriptedLLM(['{"sufficient": true}'])
    retriever = _depth(child, llm, _RecordingPrompt(), max_iters=2, max_chunks=10)

    retriever.retrieve("q")

    assert len(llm.calls) == 1
    assert llm.function_call_calls == []


def test_score_chunks_depth_delegates_and_ensemble_averages():
    """Depth delegates scoring; ensemble averages across children."""
    child = _FakeChild(_chunks(5), top_k=5, default_size=2)
    prompt = _RecordingPrompt()
    depth = _depth(child, _ScriptedLLM([]), prompt, 2, 5)
    assert depth.score_chunks([1, 2], "q") == [(1, 0.5), (2, 0.5)]

    ensemble = _ensemble(
        [_FakeChild(_chunks(5), top_k=2), _FakeChild(_chunks(5), top_k=2)],
        _ScriptedLLM([]),
        prompt,
        2,
        5,
    )
    assert ensemble.score_chunks([1, 2], "q") == [(1, 0.5), (2, 0.5)]


def test_required_parameters_raise_when_missing():
    """Omitting max_iters/max_chunks/prompt/llm_model fails loudly."""
    child = _FakeChild(_chunks(3), top_k=3)
    base = {"children": [child], "max_iters": 2, "max_chunks": 5}
    with pytest.raises(Exception, match="max_iters"):
        LLMEvaluatedDepthRetriever(
            **{
                **base,
                "prompt": _RecordingPrompt(),
                "llm_model": _ScriptedLLM([]),
                "max_iters": None,
            }
        )
    with pytest.raises(Exception, match="prompt"):
        LLMEvaluatedDepthRetriever(
            children=[child], max_iters=2, max_chunks=5, llm_model=_ScriptedLLM([])
        )
    with pytest.raises(Exception, match="llm_model"):
        LLMEvaluatedDepthRetriever(
            children=[child], max_iters=2, max_chunks=5, prompt=_RecordingPrompt()
        )


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------


def test_parse_tolerates_fences_and_unknown_keys():
    """Fenced JSON with extra keys parses, unknown keys ignored."""
    verdict = parse_evaluation_output(
        '```json\n{"sufficient": false, "top_k": 3, "x": 1}\n```'
    )
    assert verdict == RetrievalVerdict(sufficient=False, top_k=3, children=None)


def test_parse_rejects_bad_top_k_and_children():
    """Non-positive top_k and non-int children fail loudly."""
    for bad in (
        '{"sufficient": false, "top_k": 0}',
        '{"sufficient": false, "children": [1.5]}',
    ):
        with pytest.raises(RAGRetrieverEvaluationError):
            parse_evaluation_output(bad)


def test_parse_requires_boolean_sufficient():
    """A missing or non-boolean sufficient field fails loudly."""
    with pytest.raises(RAGRetrieverEvaluationError, match="sufficient"):
        parse_evaluation_output('{"top_k": 3}')


def test_parse_arguments_accepts_dict_payload():
    """A decoded mapping is validated like a parsed text verdict."""
    verdict = parse_evaluation_arguments(
        {"sufficient": False, "top_k": 4, "children": [1], "x": 2}
    )
    assert verdict == RetrievalVerdict(sufficient=False, top_k=4, children=[1])


def test_parse_arguments_accepts_json_string_payload():
    """A JSON-encoded string payload delegates to the tolerant text parser."""
    verdict = parse_evaluation_arguments(
        '```json\n{"sufficient": true, "top_k": 3}\n```'
    )
    assert verdict == RetrievalVerdict(sufficient=True, top_k=3, children=None)


def test_parse_arguments_accepts_non_dict_mapping():
    """A read-only mapping is accepted like a decoded dict."""
    verdict = parse_evaluation_arguments(MappingProxyType({"sufficient": True}))
    assert verdict == RetrievalVerdict(sufficient=True)


def test_parse_arguments_rejects_invalid_type():
    """A payload that is neither a mapping nor a string fails loudly."""
    with pytest.raises(RAGRetrieverEvaluationError, match="list"):
        parse_evaluation_arguments([1, 2])
