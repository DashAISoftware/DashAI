"""Service for LLM lookup-or-create DB operations.

Delegates model instantiation to the component registry,
keeping DB persistence concerns separate from model construction.
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    RAGGenerationModel as GenerationDBModel,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.exceptions import RAGGenerationModelError
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


class LLMService:
    """Handles lookup-or-create of LLM records in the RAGGenerationModel table."""

    def __init__(self, db: Session, registry: ComponentRegistry):
        self._db = db
        self._registry = registry

    def get_or_create(
        self, component_name: str, params: dict[str, Any]
    ) -> LLMServiceResult:
        """Lookup-or-create an LLM record.

        Steps:
          1. Sort params for deterministic DB query.
          2. Query RAGGenerationModel by (class_name, parameters).
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
        sorted_params = normalize_params(params)
        # Include class_name in the hash so different LLM components with
        # identical parameters produce distinct hashes (the DB column has a
        # UNIQUE constraint on parameters_hash).
        params_hash = build_parameters_hash(
            {"__class__": component_name, **sorted_params}
        )

        try:
            existing = (
                self._db.query(GenerationDBModel)
                .filter_by(class_name=component_name, parameters_hash=params_hash)
                .first()
            )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RuntimeError("Database error during LLM lookup.") from e

        factory = RAGModelsFactory(self._registry)

        if existing is not None:
            model_class = self._registry[existing.class_name]["class"]
            if not issubclass(model_class, TextToTextGenerationTaskModel):
                raise RAGGenerationModelError(
                    f"Component {existing.class_name} is not a "
                    f"TextToTextGenerationTaskModel subclass."
                )
            result = factory.create_llm(existing.class_name, existing.parameters)
            return LLMServiceResult(
                db_record_id=existing.id,
                model=result.model,
            )

        try:
            db_record = GenerationDBModel(
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
        model_class = model.__class__
        if not issubclass(model_class, TextToTextGenerationTaskModel):
            raise RAGGenerationModelError(
                f"Component {component_name} is not a "
                f"TextToTextGenerationTaskModel subclass."
            )

        try:
            self._db.commit()
            self._db.refresh(db_record)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during LLM creation.") from e
        return LLMServiceResult(
            db_record_id=db_record.id,
            model=model,
        )
