"""Factory and setup-service integration tests for the LLM-evaluated retrievers.

Covers both construction paths: the pure :class:`RetrieverFactory` (nested
``{component, params}`` resolution for ``llm_model`` and ``prompt``) and the
DB-backed :class:`RetrieverSetupService` (the ``llm_model`` resolved through
:class:`RetrievalLLMService` and persisted as a bridge). A regression case
confirms an existing composite (``ParallelRetriever``) still constructs with
component-free params through both paths.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Tuple

from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    RAGPipeline,
    RAGRetriever,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.prompts.evaluation import (
    CustomRetrievalSufficiencyPrompt,
    DefaultRetrievalSufficiencyPrompt,
    RetrievalSufficiencyPrompt,
)
from DashAI.back.models.RAG.prompts.evaluation.default_retrieval_sufficiency_prompt import (  # noqa: E501
    TEMPLATES as SUFFICIENCY_TEMPLATES,
)
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_depth_retriever import (  # noqa: E501
    LLMEvaluatedDepthRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_ensemble_retriever import (  # noqa: E501
    LLMEvaluatedEnsembleRetriever,
)
from DashAI.back.models.RAG.retrievers.retriever_factory import RetrieverFactory
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever
from DashAI.back.models.RAG.retrievers.trace_utils import retriever_trace
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.retriever_setup_service import RetrieverSetupService

# ---------------------------------------------------------------------------
# stubs
# ---------------------------------------------------------------------------


class _EmptyLLMSchema(BaseSchema):
    """Empty schema for the stub LLM."""


class StubFactoryLLM(TextToTextGenerationTaskModel):
    """Minimal text-to-text model used as a resolvable ``llm_model``."""

    SCHEMA = _EmptyLLMSchema

    def __init__(self, **kwargs: Any) -> None:
        """Initialise with an empty parameter set."""
        self.parameters: Dict[str, Any] = {}

    def generate(self, input: Any) -> List[Any]:
        """Return a fixed sufficient verdict."""
        return ['{"sufficient": true}']


class _LeafRetriever(CompositeRetriever):
    """Childless composite usable as a pure-path child (no persistence)."""

    SCHEMA = BaseSchema

    def retrieve(self, query: str, **kwargs: Any) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Return no chunks."""
        return [], retriever_trace(self, [])

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Return no scores."""
        return []

    @property
    def retrieval_top_k(self) -> int:
        """Return a single chunk."""
        return 1


class _StubSparseSchema(BaseSchema):
    """Schema for the stub sparse retriever."""

    top_k: schema_field(
        int_field(gt=0),
        placeholder=5,
        description="Number of chunks to retrieve.",
    )  # type: ignore


class _StubSparseRetriever(SparseRetriever):
    """Persistable sparse retriever stub used as a setup-path child."""

    SCHEMA = _StubSparseSchema

    def __init__(self, **kwargs: Any) -> None:
        """Store the configured top-k."""
        super().__init__(**kwargs)
        self._top_k = self.params.pop("top_k")

    def init_model(self) -> None:
        """No-op: the stub needs no initialization."""

    def save(self, filename: str = "") -> None:
        """No-op: the stub persists no state."""

    def retrieve(self, query: str, **kwargs: Any) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Return no chunks."""
        return [], retriever_trace(self, [])

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Return no scores."""
        return []

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k."""
        return self._top_k


def _pure_registry() -> ComponentRegistry:
    """Build a minimal registry carrying only the components under test."""
    from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
        ParallelRetriever,
    )

    registry = ComponentRegistry()
    for component in (
        StubFactoryLLM,
        DefaultRetrievalSufficiencyPrompt,
        CustomRetrievalSufficiencyPrompt,
        _LeafRetriever,
        ParallelRetriever,
        LLMEvaluatedDepthRetriever,
        LLMEvaluatedEnsembleRetriever,
    ):
        registry.register_component(component)
    return registry


def _llm_ref() -> Dict[str, Any]:
    """Return a nested ``llm_model`` reference."""
    return {"component": "StubFactoryLLM", "params": {}}


def _prompt_ref() -> Dict[str, Any]:
    """Return a nested ``prompt`` reference with a concrete template."""
    return {
        "component": "DefaultRetrievalSufficiencyPrompt",
        "params": {"language": "en", "template": SUFFICIENCY_TEMPLATES["en"]},
    }


def _leaf_ref(pure: bool) -> Dict[str, Any]:
    """Return a child reference for the pure or setup path."""
    if pure:
        return {"component": "_LeafRetriever", "params": {"children": []}}
    return {"component": "_StubSparseRetriever", "params": {"top_k": 3}}


# ---------------------------------------------------------------------------
# pure factory path
# ---------------------------------------------------------------------------


def test_pure_factory_builds_depth_retriever_with_resolved_refs():
    """The depth retriever resolves llm_model/prompt refs and nests children."""
    registry = _pure_registry()
    factory = RetrieverFactory(registry, "C:/tmp/rag", {})
    params = {
        "children": [_leaf_ref(pure=True)],
        "max_iters": 2,
        "max_chunks": 5,
        "llm_model": _llm_ref(),
        "prompt": _prompt_ref(),
    }

    model = factory.create("LLMEvaluatedDepthRetriever", copy.deepcopy(params)).model

    assert isinstance(model, LLMEvaluatedDepthRetriever)
    assert isinstance(model.llm_model, StubFactoryLLM)
    assert isinstance(model.prompt, RetrievalSufficiencyPrompt)
    assert len(model.get_children()) == 1
    assert isinstance(model.get_children()[0], _LeafRetriever)


def test_pure_factory_builds_ensemble_retriever_with_resolved_refs():
    """The ensemble retriever resolves refs and builds every child."""
    registry = _pure_registry()
    factory = RetrieverFactory(registry, "C:/tmp/rag", {})
    params = {
        "children": [_leaf_ref(pure=True), _leaf_ref(pure=True)],
        "max_iters": 2,
        "max_chunks": 5,
        "llm_model": _llm_ref(),
        "prompt": _prompt_ref(),
    }

    model = factory.create("LLMEvaluatedEnsembleRetriever", copy.deepcopy(params)).model

    assert isinstance(model, LLMEvaluatedEnsembleRetriever)
    assert isinstance(model.llm_model, StubFactoryLLM)
    assert isinstance(model.prompt, RetrievalSufficiencyPrompt)
    assert len(model.get_children()) == 2


def test_pure_factory_stores_raw_trace_params():
    """The factory snapshots the raw construction params on every model."""
    registry = _pure_registry()
    factory = RetrieverFactory(registry, "C:/tmp/rag", {})
    params = {
        "children": [_leaf_ref(pure=True)],
        "max_iters": 2,
        "max_chunks": 5,
        "llm_model": _llm_ref(),
        "prompt": _prompt_ref(),
    }

    model = factory.create("LLMEvaluatedDepthRetriever", copy.deepcopy(params)).model

    assert model._trace_params["max_iters"] == 2
    assert (
        model._trace_params["prompt"]["component"]
        == "DefaultRetrievalSufficiencyPrompt"
    )
    child = model.get_children()[0]
    assert isinstance(child, _LeafRetriever)
    assert child._trace_params["children"] == []


def test_pure_factory_parallel_retriever_unchanged():
    """A component-free composite still builds exactly as before."""
    from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
        ParallelRetriever,
    )

    registry = _pure_registry()
    factory = RetrieverFactory(registry, "C:/tmp/rag", {})
    params = {
        "children": [_leaf_ref(pure=True), _leaf_ref(pure=True)],
        "merge_strategy": "round_robin",
    }

    model = factory.create("ParallelRetriever", copy.deepcopy(params)).model

    assert isinstance(model, ParallelRetriever)
    assert len(model.get_children()) == 2


# ---------------------------------------------------------------------------
# setup-service path
# ---------------------------------------------------------------------------


def _create_pipeline(db) -> RAGPipeline:
    """Insert and return a committed session + pipeline pair."""
    session = GenerativeSession(
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={},
        name=f"adaptive_{uuid.uuid4().hex[:8]}",
        description=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    pipeline = RAGPipeline(
        session_id=session.id,
        name="",
        description=None,
        parameters=None,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


def test_setup_service_builds_depth_retriever_and_persists_bridge(client: TestClient):
    """The setup service resolves refs and persists the composite bridge."""
    registry = client.app.container["component_registry"]
    registry.register_component(StubFactoryLLM)
    registry.register_component(_StubSparseRetriever)
    session_factory = client.app.container["session_factory"]
    rag_path = str(client.app.container["config"]["RAG_PATH"])

    with session_factory() as db:
        pipeline = _create_pipeline(db)
        service = RetrieverSetupService(
            db, registry, rag_path, {}, chunk_set_id=1, pipeline_id=pipeline.id
        )
        params = {
            "children": [_leaf_ref(pure=False)],
            "max_iters": 2,
            "max_chunks": 5,
            "llm_model": _llm_ref(),
            "prompt": _prompt_ref(),
        }

        result = service.setup("LLMEvaluatedDepthRetriever", params)

        assert isinstance(result.model, LLMEvaluatedDepthRetriever)
        assert isinstance(result.model.llm_model, StubFactoryLLM)
        assert isinstance(result.model.prompt, RetrievalSufficiencyPrompt)
        bridge = db.query(RAGRetriever).get(result.db_record_id)
        assert bridge is not None
        assert bridge.class_name == "LLMEvaluatedDepthRetriever"


def test_setup_service_parallel_retriever_unchanged(client: TestClient):
    """A component-free composite still sets up through the service."""
    from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
        ParallelRetriever,
    )

    registry = client.app.container["component_registry"]
    registry.register_component(_StubSparseRetriever)
    session_factory = client.app.container["session_factory"]
    rag_path = str(client.app.container["config"]["RAG_PATH"])

    with session_factory() as db:
        pipeline = _create_pipeline(db)
        service = RetrieverSetupService(
            db, registry, rag_path, {}, chunk_set_id=1, pipeline_id=pipeline.id
        )
        params = {
            "children": [_leaf_ref(pure=False), _leaf_ref(pure=False)],
            "merge_strategy": "round_robin",
        }

        result = service.setup("ParallelRetriever", params)

        assert isinstance(result.model, ParallelRetriever)
        assert len(result.model.get_children()) == 2
