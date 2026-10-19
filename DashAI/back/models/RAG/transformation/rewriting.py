"""LLM-backed query rewriting (1-to-1)."""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.exceptions import RAGTransformationOutputError
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryRewritingPrompt,
)
from DashAI.back.models.RAG.transformation.llm_query_transformation import (
    LLMQueryTransformation,
)


class LLMQueryRewriter(LLMQueryTransformation):
    """Rewrites a user message into exactly one self-contained search query.

    The rewriting transformer is 1-to-1: it always returns a single query that
    folds the conversation context into the current request when needed.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="LLM Query Rewriter",
        es="Reescritor de Consulta con LLM",
        pt="Reescritor de Consulta com LLM",
        de="LLM-Abfrage-Umschreiber",
        zh="LLM 查询改写器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Rewrites a user message into a single self-contained search query.",
        es="Reescribe el mensaje del usuario en una única consulta de búsqueda"
        " autocontenida.",
        pt="Reescreve a mensagem do usuário em uma única consulta de busca"
        " autocontida.",
        de="Schreibt eine Benutzernachricht in eine einzelne eigenständige"
        " Suchanfrage um.",
        zh="将用户消息改写为单个自包含的搜索查询。",
    )

    EXPECTED_FUNCTION = "rewrite_query"
    ARGUMENT_KEY = "query"
    TRANSFORMATION_PROMPT_BASE: ClassVar[type] = QueryRewritingPrompt

    FUNCTION_DESCRIPTION: str = (
        "Rewrites the user message into one self-contained search query that "
        "keeps the original intent and folds in conversation context."
    )
    FUNCTION_PARAMETERS: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The self-contained search query.",
            }
        },
        "required": ["query"],
    }

    metadata = {"technique": "rewriting", "prompt_parent": "QueryRewritingPrompt"}

    def _render_prompt(self, message: str, history_block: str) -> str:
        """Render the rewriting prompt with the message and history block."""
        return self.prompt.format(input=message, history=history_block)

    def _parse_arguments(self, arguments: Dict[str, Any]) -> List[str]:
        """Parse a single rewritten query from the model arguments.

        Parameters
        ----------
        arguments : Dict[str, Any]
            The arguments mapping emitted by the model.

        Returns
        -------
        List[str]
            A one-element list with the rewritten query.

        Raises
        ------
        RAGTransformationOutputError
            If the ``query`` argument is missing or blank.
        """
        query = arguments.get(self.ARGUMENT_KEY)
        if not isinstance(query, str) or not query.strip():
            raise RAGTransformationOutputError(
                "The rewriting model did not return a non-empty 'query' string."
            )
        return [query]
