"""LLM-backed query decomposition (1-to-n, count decided by the model)."""

from __future__ import annotations

import logging
from typing import Any, ClassVar, Dict, List

from DashAI.back.core.schema_fields import (
    component_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryDecompositionPrompt,
)
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PROGRESS_JUSTIFICATION_KEY,
    RAG_PROGRESS_MESSAGE_KEY,
)
from DashAI.back.models.RAG.transformation.llm_query_transformation import (
    LLMQueryTransformation,
    LLMQueryTransformationSchema,
)

logger = logging.getLogger(__name__)


class LLMQueryDecomposerSchema(LLMQueryTransformationSchema):
    """Schema for :class:`LLMQueryDecomposer`.

    Attributes:
        prompt: The transformation prompt, defaulting to the decomposition
            prompt.
        max_subqueries: Optional upper bound on the number of sub-queries.
    """

    prompt: schema_field(
        component_field(parent="QueryTransformationPrompt"),
        placeholder={"component": "DefaultQueryDecompositionPrompt", "params": {}},
        description=MultilingualString(
            en="The prompt used to instruct the transformation model.",
            es="El prompt usado para instruir al modelo de transformación.",
            pt="O prompt usado para instruir o modelo de transformação.",
            de="Der Prompt, der das Transformationsmodell anweist.",
            zh="用于指示转换模型的提示词。",
        ),
    )
    max_subqueries: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en="Optional upper bound on the number of sub-queries. Leave empty"
            " for no limit.",
            es="Límite superior opcional del número de subconsultas. Déjalo"
            " vacío para no poner límite.",
            pt="Limite superior opcional do número de subconsultas. Deixe vazio"
            " para não limitar.",
            de="Optionale Obergrenze für die Anzahl der Teilfragen. Leer lassen"
            " für kein Limit.",
            zh="子查询数量的可选上限。留空表示不限制。",
        ),
        alias=MultilingualString(
            en="Max sub-queries",
            es="Subconsultas máximas",
            pt="Subconsultas máximas",
            de="Maximale Teilfragen",
            zh="最大子查询数",
        ),
    ) = None


class LLMQueryDecomposer(LLMQueryTransformation):
    """Decomposes a complex question into independently retrievable sub-queries.

    The model decides how many sub-queries are needed. An optional
    ``max_subqueries`` cap truncates the result when set.
    """

    SCHEMA = LLMQueryDecomposerSchema
    DISPLAY_NAME: str = MultilingualString(
        en="LLM Query Decomposer",
        es="Descomponedor de Consulta con LLM",
        pt="Decompositor de Consulta com LLM",
        de="LLM-Abfrage-Zerleger",
        zh="LLM 查询分解器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Decomposes a complex question into independently retrievable sub-queries.",
        es="Descompone una pregunta compleja en subconsultas recuperables de"
        " forma independiente.",
        pt="Decompõe uma pergunta complexa em subconsultas recuperáveis de"
        " forma independente.",
        de="Zerlegt eine komplexe Frage in unabhängig abrufbare Teilfragen.",
        zh="将复杂问题分解为可独立检索的子查询。",
    )

    EXPECTED_FUNCTION = "decompose_query"
    ARGUMENT_KEY = "queries"
    TRANSFORMATION_PROMPT_BASE: ClassVar[type] = QueryDecompositionPrompt
    TOLERATE_BARE_LISTS: bool = True

    FUNCTION_DESCRIPTION: str = (
        "Decomposes a complex question into independently retrievable sub-queries."
    )
    FUNCTION_PARAMETERS: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The list of independently retrievable sub-queries.",
                "minItems": 1,
            },
            RAG_PROGRESS_MESSAGE_KEY: {
                "type": "string",
                "description": (
                    "Optional one short user-facing sentence in the prompt "
                    "language describing what you did."
                ),
            },
            RAG_PROGRESS_JUSTIFICATION_KEY: {
                "type": "string",
                "description": (
                    "Optional one short sentence in the prompt language "
                    "explaining why you did it."
                ),
            },
        },
        "required": ["queries"],
    }

    metadata = {
        "technique": "decomposition",
        "prompt_parent": "QueryDecompositionPrompt",
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the decomposition transformer.

        Parameters
        ----------
        max_subqueries : int | None, optional
            Optional upper bound on the number of sub-queries. Defaults to
            ``None`` (unrestricted).

        Other Parameters
        ----------------
        prompt, llm_model, history_window
            Forwarded to :class:`LLMQueryTransformation`.
        """
        self.max_subqueries = kwargs.pop("max_subqueries", None)
        super().__init__(**kwargs)

    def _render_prompt(self, message: str, history_block: str) -> str:
        """Render the decomposition prompt with the message, history and cap."""
        return self.prompt.format(
            input=message,
            history=history_block,
            n_max=self.max_subqueries,
        )

    def _parse_arguments(self, arguments: Dict[str, Any]) -> List[str]:
        """Parse the list of sub-queries from the model arguments.

        Parameters
        ----------
        arguments : Dict[str, Any]
            The arguments mapping emitted by the model.

        Returns
        -------
        List[str]
            The raw sub-query entries as strings.

        Raises
        ------
        RAGTransformationOutputError
            If the model arguments do not contain a non-empty ``queries`` list.
        """
        return [str(entry) for entry in self._require_list(arguments)]

    def _finalize_queries(self, queries: List[str]) -> List[str]:
        """Truncate to ``max_subqueries`` when the cap is set.

        Parameters
        ----------
        queries : List[str]
            Cleaned, deduplicated sub-queries.

        Returns
        -------
        List[str]
            The final sub-queries.
        """
        if self.max_subqueries is not None and len(queries) > self.max_subqueries:
            logger.info(
                "Query decomposition produced %d sub-queries; truncating to "
                "max_subqueries=%d.",
                len(queries),
                self.max_subqueries,
            )
            return queries[: self.max_subqueries]
        return queries
