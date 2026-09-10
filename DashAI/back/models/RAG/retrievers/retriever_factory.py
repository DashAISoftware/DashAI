"""Pure factory for retriever instances.

Builds retriever models from the component registry.
Phase 1 only -- no I/O (embeddings, similarity matrices).
"""

from dataclasses import dataclass
from typing import Any

from DashAI.back.core.schema_fields.utils import fill_objects, normalize_payload
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGComponentNotFoundError,
    RAGRetrieverError,
    RAGRetrieverMissingParameterError,
)
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever
from DashAI.back.models.RAG.retrievers.persistence import (
    DensePersistence,
    SparsePersistence,
)
from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever


@dataclass(frozen=True)
class RetrieverFactoryResult:
    """Result of building a retriever via :class:`RetrieverFactory`.

    Attributes:
        model: The fully constructed :class:`RetrieverModel` instance.
    """

    model: RetrieverModel


class RetrieverFactory:
    """Creates retriever instances. Phase 1 only — no I/O.

    Builds retriever models from the component registry, handling both
    unit (leaf) and composite retrievers.  Schema validation and
    infrastructure injection are performed during construction.

    Args:
        registry: Application component registry for resolving
            component name strings.
        RAG_path: Root path for RAG data storage.
        chunks: Nested mapping of document IDs to chunk IDs to
            :class:`Chunk` instances.
    """

    def __init__(
        self,
        registry: ComponentRegistry,
        RAG_path: str,  # noqa: N803
        chunks: dict[int, dict[int, Chunk]],
    ):
        self._registry = registry
        self._RAG_path = RAG_path
        self._chunks = chunks

    def create(
        self,
        component_name: str,
        params: dict[str, Any],
        persistence: DensePersistence | SparsePersistence | None = None,
    ) -> RetrieverFactoryResult:
        params = normalize_payload(params)
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from err

        if issubclass(model_class, CompositeRetriever):
            return self._create_composite(model_class, params)

        return self._create_unit(model_class, params, persistence)

    def _create_composite(self, model_class, params) -> RetrieverFactoryResult:
        """Build a composite retriever by recursively creating children.

        Args:
            model_class: The :class:`CompositeRetriever` subclass to
                instantiate.
            params: Configuration parameters; the ``children`` key is
                consumed and replaced with built :class:`RetrieverModel`
                instances.

        Returns:
            A :class:`RetrieverFactoryResult` wrapping the new composite.
        """
        children_configs = params.pop("children", [])
        children_instances = [
            self.create(c["component"], c["params"]).model for c in children_configs
        ]
        params["children"] = children_instances
        model = model_class(**params)
        return RetrieverFactoryResult(model=model)

    def _create_unit(
        self,
        model_class,
        params,
        persistence: DensePersistence | SparsePersistence | None = None,
    ) -> RetrieverFactoryResult:
        """Build a unit (leaf) retriever with schema validation and injection.

        Args:
            model_class: The :class:`UnitRetriever` subclass to instantiate.
            params: Configuration parameters validated against the
                model's schema.
            persistence: A :class:`DensePersistence` or
                :class:`SparsePersistence` instance matching the
                retriever type.

        Returns:
            A :class:`RetrieverFactoryResult` wrapping the new unit retriever.

        Raises:
            RAGRetrieverMissingParameterError: If the required persistence
                type is not provided for the retriever class.
            RAGRetrieverError: If the model class is neither a dense nor
                sparse retriever.
        """
        validated = model_class.SCHEMA.model_validate(params)
        resolved = fill_objects(validated, self._registry)
        model = model_class(**resolved)

        if issubclass(model_class, DenseRetriever):
            if not isinstance(persistence, DensePersistence):
                raise RAGRetrieverMissingParameterError(
                    "A DensePersistence is required for dense retrievers "
                    "but none was provided."
                )
            model.inject_infra(self._RAG_path, self._chunks, persistence)
        elif issubclass(model_class, SparseRetriever):
            if not isinstance(persistence, SparsePersistence):
                raise RAGRetrieverMissingParameterError(
                    "A SparsePersistence is required for sparse retrievers "
                    "but none was provided."
                )
            model.inject_infra(self._RAG_path, self._chunks, persistence)
        else:
            raise RAGRetrieverError(
                f"Unsupported unit retriever: {model_class.__name__}"
            )

        return RetrieverFactoryResult(model=model)
