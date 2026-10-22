"""Service for LLM lookup-or-create DB operations.

Delegates model instantiation to the component registry,
keeping DB persistence concerns separate from model construction.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    RAGGenerationModel as GenerationDBModel,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.lazy_llm import LazyLLM
from DashAI.back.models.RAG.exceptions import (
    RAGComponentNotFoundError,
    RAGGenerationModelError,
)
from DashAI.back.models.RAG.RAG_models_factory import RAGModelsFactory
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.utils import (
    build_parameters_hash,
    normalize_params,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMServiceResult:
    """Result of LLM lookup-or-create from LLMService.

    Includes the DB record id alongside the instantiated model.
    """

    db_record_id: int
    model: "TextToTextGenerationTaskModel"


def _build_lazy_factory(
    registry: ComponentRegistry,
    component_name: str,
    params: dict[str, Any],
) -> Callable[[], TextToTextGenerationTaskModel]:
    """Capture the construction inputs for a :class:`LazyLLM`.

    Parameters
    ----------
    registry : ComponentRegistry
        Registry used to resolve the component on first use.
    component_name : str
        Registered LLM component name.
    params : dict[str, Any]
        Effective constructor parameters.

    Returns
    -------
    Callable[[], TextToTextGenerationTaskModel]
        Zero-argument factory that builds the real model.
    """
    class_name = component_name
    captured_params = dict(params)

    def _create() -> TextToTextGenerationTaskModel:
        return RAGModelsFactory(registry).create_llm(class_name, captured_params).model

    return _create


class LLMService:
    """Handles lookup-or-create of LLM records.

    The target DB table and the result wrapper are injectable so subclasses
    (for example the retrieval-evaluation LLM service) can persist the very
    same component into a dedicated table without duplicating the lookup rules.
    The defaults keep every existing caller bound to ``RAGGenerationModel``.
    """

    def __init__(
        self,
        db: Session,
        registry: ComponentRegistry,
        db_model: type | None = None,
        result_class: type[LLMServiceResult] | None = None,
    ):
        self._db = db
        self._registry = registry
        self._db_model = db_model or GenerationDBModel
        self._result_class = result_class or LLMServiceResult

    def _lookup_record(
        self, component_name: str, params: dict[str, Any]
    ) -> tuple[dict[str, Any], str, Any | None]:
        """Normalise the params and find the matching DB record.

        Parameters
        ----------
        component_name : str
            Registered LLM component name.
        params : dict[str, Any]
            LLM configuration parameters.

        Returns
        -------
        tuple[dict[str, Any], str, Any | None]
            The sorted params, their hash and the existing record or ``None``.

        Raises
        ------
        RuntimeError
            If a database error occurs during lookup.
        """
        sorted_params = normalize_params(params)
        # Include class_name in the hash so different LLM components with
        # identical parameters produce distinct hashes (the DB column has a
        # UNIQUE constraint on parameters_hash).
        params_hash = build_parameters_hash(
            {"__class__": component_name, **sorted_params}
        )

        try:
            existing = (
                self._db.query(self._db_model)
                .filter_by(class_name=component_name, parameters_hash=params_hash)
                .first()
            )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RuntimeError("Database error during LLM lookup.") from e

        return sorted_params, params_hash, existing

    @staticmethod
    def _validate_llm_class(component_name: str, model_class: type) -> None:
        """Ensure a registered class is a text-to-text generation model.

        Parameters
        ----------
        component_name : str
            Component name used in the error message.
        model_class : type
            Registered component class.

        Raises
        ------
        RAGGenerationModelError
            If the class is not a ``TextToTextGenerationTaskModel`` subclass.
        """
        if not issubclass(model_class, TextToTextGenerationTaskModel):
            raise RAGGenerationModelError(
                f"Component {component_name} is not a "
                f"TextToTextGenerationTaskModel subclass."
            )

    @staticmethod
    def _validate_llm_schema(model_class: type, params: dict[str, Any]) -> None:
        """Validate parameters against the component schema without building it.

        Mirrors the ``SCHEMA(**params)`` check in
        :meth:`~DashAI.back.models.RAG.llm_factory.LLMFactory.create` so the
        lazy path rejects bad configuration during assembly. Constructing the
        schema is intentionally the only thing that happens; the model itself
        is still built on first use.

        Parameters
        ----------
        model_class : type
            Registered LLM component class.
        params : dict[str, Any]
            Effective constructor parameters.

        Raises
        ------
        pydantic.ValidationError
            If the parameters do not satisfy the component schema.
        """
        schema = getattr(model_class, "SCHEMA", None)
        if schema is None:
            return
        schema(**params)

    def _registered_llm_class(self, component_name: str) -> type:
        """Resolve a component class or raise the factory's not-found error.

        Parameters
        ----------
        component_name : str
            Registered LLM component name.

        Returns
        -------
        type
            The registered component class.

        Raises
        ------
        RAGComponentNotFoundError
            If the component is not registered.
        """
        try:
            return self._registry[component_name]["class"]
        except KeyError as error:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from error

    def _create_committed_record(
        self,
        component_name: str,
        sorted_params: dict[str, Any],
        params_hash: str,
    ) -> Any:
        """Persist and commit a new LLM configuration record.

        Parameters
        ----------
        component_name : str
            Registered LLM component name.
        sorted_params : dict[str, Any]
            Normalised constructor parameters.
        params_hash : str
            Deterministic hash of the component name and params.

        Returns
        -------
        Any
            The committed DB record with its generated id.

        Raises
        ------
        RuntimeError
            If a database error occurs during creation.
        """
        try:
            db_record = self._db_model(
                class_name=component_name,
                parameters=sorted_params,
                parameters_hash=params_hash,
            )
            self._db.add(db_record)
            self._db.commit()
            self._db.refresh(db_record)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during LLM creation.") from e
        return db_record

    def get_or_create(
        self, component_name: str, params: dict[str, Any]
    ) -> LLMServiceResult:
        """Lookup-or-create an LLM record.

        Steps:
          1. Sort params for deterministic DB query.
          2. Query the target DB model by (class_name, parameters).
          3. If found — instantiate model from registry with existing params.
          4. If not found — create DB record, instantiate model from registry.

        Args:
            component_name: Registered LLM component name.
            params: LLM configuration parameters.

        Returns:
            An LLMServiceResult with the DB record id and the model instance.

        Raises:
            RuntimeError: If a database error occurs during lookup or creation.
            RAGGenerationModelError: If the registered component is not a
                TextToTextGenerationTaskModel subclass.
        """
        sorted_params, params_hash, existing = self._lookup_record(
            component_name, params
        )

        factory = RAGModelsFactory(self._registry)

        if existing is not None:
            model_class = self._registry[existing.class_name]["class"]
            self._validate_llm_class(existing.class_name, model_class)
            result = factory.create_llm(existing.class_name, existing.parameters)
            return self._result_class(
                db_record_id=existing.id,
                model=result.model,
            )

        try:
            db_record = self._db_model(
                class_name=component_name,
                parameters=sorted_params,
                parameters_hash=params_hash,
            )
            self._db.add(db_record)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during LLM creation.") from e

        result = factory.create_llm(component_name, sorted_params)
        model = result.model
        self._validate_llm_class(component_name, model.__class__)

        try:
            self._db.commit()
            self._db.refresh(db_record)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during LLM creation.") from e
        return self._result_class(
            db_record_id=db_record.id,
            model=model,
        )

    def get_or_create_lazy(
        self, component_name: str, params: dict[str, Any]
    ) -> LLMServiceResult:
        """Lookup-or-create a record without constructing the LLM.

        This performs the same parameter normalisation, hashing, database
        lookup/creation and component validation as :meth:`get_or_create`, but
        returns a :class:`~DashAI.back.models.lazy_llm.LazyLLM` that builds the
        real backend on first use. The effective parameters are still validated
        against the component ``SCHEMA`` before the proxy is returned, so an
        invalid configuration fails during assembly rather than on first use.
        The configuration record is committed before any construction happens;
        if a later load fails, the valid record is intentionally left persisted
        for reuse.

        Parameters
        ----------
        component_name : str
            Registered LLM component name.
        params : dict[str, Any]
            LLM configuration parameters.

        Returns
        -------
        LLMServiceResult
            The DB record id and a lazy proxy for the model.

        Raises
        ------
        RuntimeError
            If a database error occurs during lookup or creation.
        RAGComponentNotFoundError
            If the component is not registered.
        RAGGenerationModelError
            If the registered component is not a
            ``TextToTextGenerationTaskModel`` subclass.
        """
        sorted_params, params_hash, existing = self._lookup_record(
            component_name, params
        )

        if existing is not None:
            class_name = existing.class_name
            effective_params = existing.parameters
            model_class = self._registered_llm_class(class_name)
            self._validate_llm_class(class_name, model_class)
            # Validate the stored configuration too: it may predate a schema
            # change, and a bad one should fail at assembly, not on first use.
            self._validate_llm_schema(model_class, effective_params)
            db_record_id = existing.id
        else:
            model_class = self._registered_llm_class(component_name)
            self._validate_llm_class(component_name, model_class)
            class_name = component_name
            effective_params = sorted_params
            # Validate before committing, so rejected parameters leave no row.
            self._validate_llm_schema(model_class, effective_params)
            db_record = self._create_committed_record(
                component_name, sorted_params, params_hash
            )
            db_record_id = db_record.id

        lazy_class = cast(type[TextToTextGenerationTaskModel], model_class)
        lazy_model = LazyLLM(
            _build_lazy_factory(self._registry, class_name, effective_params),
            label=class_name,
            supports_function_calling=lazy_class.supports_function_calling(),
        )
        return self._result_class(
            db_record_id=db_record_id,
            model=lazy_model,
        )
