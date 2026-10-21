"""Unified factory that delegates to type-specific sub-factories.

Phase 1 of the 3-phase lifecycle (Construction -> Initialization -> Persistence).
Builds models in memory -- no I/O, no DB access.
"""

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.chunking_model_factory import (
    ChunkingFactoryResult,
    ChunkingModelFactory,
)
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.documents.rag_document import RAGDocument
from DashAI.back.models.RAG.llm_factory import LLMFactory, LLMFactoryResult
from DashAI.back.models.RAG.prompts.prompt_factory import (
    PromptFactory,
    PromptFactoryResult,
)
from DashAI.back.models.RAG.retrievers.persistence import (
    DensePersistence,
    SparsePersistence,
)
from DashAI.back.models.RAG.retrievers.retriever_factory import (
    RetrieverFactory,
    RetrieverFactoryResult,
)
from DashAI.back.models.RAG.transformation import (
    TransformationFactory,
    TransformationFactoryResult,
)


class RAGModelsFactory:
    """Delegates model construction to type-specific sub-factories.

    Every ``create_*`` method:
    - Accepts a component name + params dict
    - Delegates to the corresponding sub-factory
    - Returns the model -- no I/O, no DB
    """

    def __init__(self, registry: ComponentRegistry):
        """Initialise the factory with a component registry.

        Args:
            registry: The ComponentRegistry used to resolve component
                names to their implementations.
        """
        self._registry = registry

    def create_chunking_model(
        self,
        component: str,
        params: dict,
        documents: dict[int, RAGDocument],
    ) -> ChunkingFactoryResult:
        """Build a chunking model via ChunkingModelFactory. Phase 1 only."""
        factory = ChunkingModelFactory(self._registry, documents)
        return factory.create(component, params.copy())

    def create_retriever(
        self,
        component: str,
        params: dict,
        RAG_path: str,  # noqa: N803
        chunks: dict[int, dict[int, Chunk]],
        persistence: DensePersistence | SparsePersistence | None = None,
        documents: dict[int, RAGDocument] | None = None,
    ) -> RetrieverFactoryResult:
        """Build a retriever via RetrieverFactory. Phase 1 only.

        Parameters
        ----------
        component : str
            Registered retriever component name.
        params : dict
            Raw construction parameters.
        RAG_path : str
            Root path for RAG data.
        chunks : dict[int, dict[int, Chunk]]
            Chunk corpus keyed by document id and chunk id.
        persistence : DensePersistence | SparsePersistence | None
            Persistence object required by unit retrievers.
        documents : dict[int, RAGDocument] | None
            Optional document mapping injected into unit retrievers so the
            LLM-evaluated retrievers can describe the corpus in their prompts.

        Returns
        -------
        RetrieverFactoryResult
            The constructed retriever model.
        """
        factory = RetrieverFactory(self._registry, RAG_path, chunks, documents)
        return factory.create(component, params, persistence)

    def create_prompt(self, component: str, params: dict) -> PromptFactoryResult:
        """Build a prompt via PromptFactory. Phase 1 only."""
        return PromptFactory(self._registry).create(component, params)

    def create_llm(self, component: str, params: dict) -> LLMFactoryResult:
        """Build an LLM via LLMFactory. Phase 1 only."""
        return LLMFactory(self._registry).create(component, params)

    def create_query_transformation(
        self, component: str, params: dict
    ) -> TransformationFactoryResult:
        """Build a query transformer via TransformationFactory. Phase 1 only."""
        return TransformationFactory(self._registry).create(component, params)
