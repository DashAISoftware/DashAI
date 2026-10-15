"""Lookup-or-create service for the retrieval-evaluation LLM.

The LLM-evaluated composite retrievers judge whether a set of retrieved chunks
is sufficient and, when it is not, which retrievers to consult next. That is a
distinct role from answer generation, so its records live in their own table
(``rag_retrieval_model``). The lookup rules are shared verbatim with
:class:`~DashAI.back.services.RAG.llm_service.LLMService` by injecting the
target DB model and the result wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import RAGRetrievalModel
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.llm_service import LLMService


@dataclass(frozen=True)
class RetrievalLLMServiceResult:
    """Result of a retrieval LLM lookup-or-create.

    Includes the DB record id alongside the instantiated model.
    """

    db_record_id: int
    model: TextToTextGenerationTaskModel


class RetrievalLLMService(LLMService):
    """Handles lookup-or-create of records in the ``rag_retrieval_model`` table."""

    def __init__(self, db: Session, registry: ComponentRegistry):
        """Initialise the service.

        Args:
            db: SQLAlchemy session used for lookup and persistence.
            registry: Component registry used to resolve and instantiate the
                LLM component.
        """
        super().__init__(
            db,
            registry,
            db_model=RAGRetrievalModel,
            result_class=RetrievalLLMServiceResult,
        )
