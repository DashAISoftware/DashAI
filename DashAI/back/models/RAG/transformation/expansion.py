"""LLM-backed query expansion (1-to-n)."""

from __future__ import annotations

import logging
from typing import Any, ClassVar, List

from DashAI.back.core.schema_fields import (
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryExpansionPrompt,
)
from DashAI.back.models.RAG.transformation.llm_output_parser import (
    parse_function_call_output,
)
from DashAI.back.models.RAG.transformation.llm_query_transformation import (
    LLMQueryTransformation,
    LLMQueryTransformationSchema,
)

logger = logging.getLogger(__name__)


class LLMQueryExpanderSchema(LLMQueryTransformationSchema):
    """Schema for :class:`LLMQueryExpander`.

    Attributes:
        prompt: The transformation prompt, defaulting to the expansion prompt.
        n_queries: Number of queries the model must produce.
    """

    prompt: schema_field(
        component_field(parent="QueryTransformationPrompt"),
        placeholder={"component": "DefaultQueryExpansionPrompt", "params": {}},
        description=MultilingualString(
            en="The prompt used to instruct the transformation model.",
            es="El prompt usado para instruir al modelo de transformación.",
            pt="O prompt usado para instruir o modelo de transformação.",
            de="Der Prompt, der das Transformationsmodell anweist.",
            zh="用于指示转换模型的提示词。",
        ),
    )
    n_queries: schema_field(
        int_field(ge=1),
        placeholder=3,
        description=MultilingualString(
            en="Number of queries the model must produce.",
            es="Número de consultas que debe producir el modelo.",
            pt="Número de consultas que o modelo deve produzir.",
            de="Anzahl der Anfragen, die das Modell erzeugen muss.",
            zh="模型必须生成的查询数量。",
        ),
    )


class LLMQueryExpander(LLMQueryTransformation):
    """Expands a user message into up to ``n_queries`` search queries.

    The requested count is an upper-bound expectation: expansion is
    best-effort, so the model may return fewer distinct queries without the
    transformation failing.
    """

    SCHEMA = LLMQueryExpanderSchema
    DISPLAY_NAME: str = MultilingualString(
        en="LLM Query Expander",
        es="Expansor de Consulta con LLM",
        pt="Expansor de Consulta com LLM",
        de="LLM-Abfrage-Erweiterer",
        zh="LLM 查询扩展器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Expands a user message into several search queries that broaden"
        " retrieval coverage.",
        es="Expande el mensaje del usuario en varias consultas de búsqueda que"
        " amplían la cobertura de recuperación.",
        pt="Expande a mensagem do usuário em várias consultas de busca que"
        " ampliam a cobertura de recuperação.",
        de="Erweitert eine Benutzernachricht zu mehreren Suchanfragen, die die"
        " Abrufabdeckung erweitern.",
        zh="将用户消息扩展为多个搜索查询，以扩大检索覆盖范围。",
    )

    EXPECTED_FUNCTION = "expand_query"
    ARGUMENT_KEY = "queries"
    TRANSFORMATION_PROMPT_BASE: ClassVar[type] = QueryExpansionPrompt

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the expansion transformer.

        Parameters
        ----------
        n_queries : int, optional
            Number of queries the model must produce. Defaults to ``3``.

        Other Parameters
        ----------------
        prompt, llm_model, history_window
            Forwarded to :class:`LLMQueryTransformation`.
        """
        self.n_queries = kwargs.pop("n_queries", 3)
        super().__init__(**kwargs)

    def _render_prompt(self, message: str, history_block: str) -> str:
        """Render the expansion prompt with the message, history and count."""
        return self.prompt.format(
            input=message,
            history=history_block,
            n=self.n_queries,
        )

    def _parse_output(self, raw: str) -> List[str]:
        """Parse the list of expanded queries from the model output.

        Parameters
        ----------
        raw : str
            Raw model output.

        Returns
        -------
        List[str]
            The raw query entries as strings.

        Raises
        ------
        RAGTransformationOutputError
            If the model output is not a non-empty ``queries`` list.
        """
        arguments = parse_function_call_output(
            raw, self.EXPECTED_FUNCTION, self.ARGUMENT_KEY
        )
        return [str(entry) for entry in self._require_list(arguments)]

    def _finalize_queries(self, queries: List[str]) -> List[str]:
        """Truncate to ``n_queries`` (an upper bound), warning when short.

        Parameters
        ----------
        queries : List[str]
            Cleaned, deduplicated queries.

        Returns
        -------
        List[str]
            At most ``n_queries`` queries.
        """
        if len(queries) > self.n_queries:
            logger.info(
                "Query expansion produced %d queries; truncating to n_queries=%d.",
                len(queries),
                self.n_queries,
            )
            return queries[: self.n_queries]
        if len(queries) < self.n_queries:
            logger.info(
                "Query expansion produced %d queries, fewer than the requested "
                "n_queries=%d; keeping them as-is.",
                len(queries),
                self.n_queries,
            )
        return queries
