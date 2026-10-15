"""LLM-backed query transformation family.

The base class owns the pipeline shared by every technique: format the
history window, render the prompt, call the language model, parse its
function-call output and sanitize the resulting queries. Subclasses only
provide the technique-specific prompt rendering, output parsing and final
normalization.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, ClassVar, Dict, List, Sequence

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.exceptions import (
    RAGTransformationConfigError,
    RAGTransformationOutputError,
)
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryTransformationPrompt,
)
from DashAI.back.models.RAG.transformation.base_query_transformation import (
    BaseQueryTransformation,
    QueryTransformationResult,
)

logger = logging.getLogger(__name__)


def format_history(history: Sequence[Dict[str, str]], window: int) -> str:
    """Render the last ``window`` conversation entries as a plain-text block.

    Every selected entry is validated: it must be a mapping carrying a
    non-empty string ``role`` and a string ``content``. A malformed entry
    raises instead of being silently coerced, because feeding an artificial
    role or empty content to the model is worse than failing the phase.

    Parameters
    ----------
    history : Sequence[Dict[str, str]]
        Conversation entries as ``{"role", "content"}`` mappings, oldest
        first.
    window : int
        Number of most recent entries to include. ``0`` (or fewer) yields an
        empty string. When the history is shorter than the window, every
        entry is used.

    Returns
    -------
    str
        One ``"role: content"`` line per entry, joined by newlines, with no
        trailing whitespace.

    Raises
    ------
    RAGTransformationConfigError
        If a selected entry is not a mapping, or its ``role``/``content``
        are missing or of the wrong type. The message names the entry index.
    """
    if not history or window <= 0:
        return ""
    selected = history[-window:]
    start = len(history) - len(selected)
    lines: List[str] = []
    for position, entry in enumerate(selected):
        index = start + position
        if not isinstance(entry, Mapping):
            raise RAGTransformationConfigError(
                f"Conversation history entry at index {index} is not a mapping "
                f"(got {type(entry).__name__})."
            )
        role = entry.get("role")
        content = entry.get("content")
        if not isinstance(role, str) or not role:
            raise RAGTransformationConfigError(
                f"Conversation history entry at index {index} must have a "
                "non-empty string 'role'."
            )
        if not isinstance(content, str):
            raise RAGTransformationConfigError(
                f"Conversation history entry at index {index} must have a "
                "string 'content'."
            )
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


class LLMQueryTransformationSchema(BaseSchema):
    """Schema shared by the LLM-backed transformers.

    Attributes:
        prompt: The transformation prompt component.
        llm_model: The text-to-text model used to transform the query.
        history_window: Number of previous messages given as context.
    """

    prompt: schema_field(
        component_field(parent="QueryTransformationPrompt"),
        placeholder={"component": "DefaultQueryRewritingPrompt", "params": {}},
        description=MultilingualString(
            en="The prompt used to instruct the transformation model.",
            es="El prompt usado para instruir al modelo de transformación.",
            pt="O prompt usado para instruir o modelo de transformação.",
            de="Der Prompt, der das Transformationsmodell anweist.",
            zh="用于指示转换模型的提示词。",
        ),
    )
    llm_model: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder={"component": "", "params": {}},
        description=MultilingualString(
            en="The language model that transforms the user message.",
            es="El modelo de lenguaje que transforma el mensaje del usuario.",
            pt="O modelo de linguagem que transforma a mensagem do usuário.",
            de="Das Sprachmodell, das die Benutzernachricht umwandelt.",
            zh="用于转换用户消息的语言模型。",
        ),
    )
    history_window: schema_field(
        int_field(ge=0),
        placeholder=2,
        description=MultilingualString(
            en="Number of previous conversation messages provided to the prompt"
            " as context.",
            es="Número de mensajes previos de la conversación proporcionados"
            " al prompt como contexto.",
            pt="Número de mensagens anteriores da conversa fornecidas ao prompt"
            " como contexto.",
            de="Anzahl der vorherigen Konversationsnachrichten, die dem Prompt"
            " als Kontext übergeben werden.",
            zh="作为上下文提供给提示词的先前对话消息数量。",
        ),
    )


class LLMQueryTransformation(BaseQueryTransformation):
    """Shared implementation for the LLM-backed transformers.

    Subclasses set ``EXPECTED_FUNCTION`` and ``ARGUMENT_KEY``, implement
    ``_render_prompt`` (to call the technique's prompt) and ``_parse_output``
    (to validate the parsed shape).
    """

    SCHEMA = LLMQueryTransformationSchema
    DESCRIPTION: str = MultilingualString(
        en="Transforms a user message into search queries using a language model"
        " and a prompt.",
        es="Transforma el mensaje del usuario en consultas de búsqueda usando"
        " un modelo de lenguaje y un prompt.",
        pt="Transforma a mensagem do usuário em consultas de busca usando um"
        " modelo de linguagem e um prompt.",
        de="Wandelt eine Benutzernachricht mithilfe eines Sprachmodells und"
        " eines Prompts in Suchanfragen um.",
        zh="使用语言模型和提示词将用户消息转换为搜索查询。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="LLM Query Transformation",
        es="Transformación de Consulta con LLM",
        pt="Transformação de Consulta com LLM",
        de="LLM-Abfrage-Transformation",
        zh="LLM 查询转换",
    )

    #: Function name the model is expected to call.
    EXPECTED_FUNCTION: str = ""
    #: Argument key holding the query (rewriting) or queries (expansion).
    ARGUMENT_KEY: str = ""
    #: Prompt family this transformer requires. The base tolerates any
    #: :class:`QueryTransformationPrompt`; each concrete technique tightens it
    #: to its own anchor so a mismatched prompt is rejected at the validation
    #: boundary instead of failing at runtime.
    TRANSFORMATION_PROMPT_BASE: ClassVar[type] = QueryTransformationPrompt

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the transformer.

        Parameters
        ----------
        prompt : QueryTransformationPrompt
            The transformation prompt instance.
        llm_model : TextToTextGenerationTaskModel
            The language model instance.
        history_window : int, optional
            Number of previous messages used as context. Defaults to ``2``.

        Raises
        ------
        RAGTransformationConfigError
            If ``prompt`` or ``llm_model`` is missing.
        """
        self.prompt = kwargs.pop("prompt", None)
        self.llm_model = kwargs.pop("llm_model", None)
        self.history_window = kwargs.pop("history_window", 2)
        if self.prompt is None:
            raise RAGTransformationConfigError(
                "A prompt instance is required to build a query transformer; "
                "no default prompt is assumed."
            )
        if self.llm_model is None:
            raise RAGTransformationConfigError(
                "An LLM model instance is required to build a query transformer; "
                "no default model is assumed."
            )

    def transform(
        self,
        message: str,
        history: Sequence[Dict[str, str]],
    ) -> QueryTransformationResult:
        """Transform a user message into one or more search queries.

        Parameters
        ----------
        message : str
            The current user message.
        history : Sequence[Dict[str, str]]
            Previous conversation entries, oldest first.

        Returns
        -------
        QueryTransformationResult
            The cleaned, deduplicated queries.

        Raises
        ------
        RAGTransformationOutputError
            If the model produced no usable output.
        """
        history_block = format_history(history, self.history_window)
        prompt_text = self._render_prompt(message, history_block)
        output = self.llm_model.generate([{"role": "user", "content": prompt_text}])
        raw = self._extract_raw_output(output)
        parsed = self._parse_output(raw)
        cleaned = self._clean_queries(parsed)
        return QueryTransformationResult(queries=self._finalize_queries(cleaned))

    def _render_prompt(self, message: str, history_block: str) -> str:
        """Render the technique prompt. Implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")

    def _parse_output(self, raw: str) -> List[str]:
        """Parse and validate the model output. Implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")

    def _finalize_queries(self, queries: List[str]) -> List[str]:
        """Apply the final technique-specific normalization.

        Parameters
        ----------
        queries : List[str]
            Cleaned, deduplicated queries.

        Returns
        -------
        List[str]
            The final query list. The default implementation is a no-op.
        """
        return queries

    @staticmethod
    def _extract_raw_output(output: Any) -> str:
        """Extract the raw string from the model output list.

        Parameters
        ----------
        output : Any
            The list returned by ``generate``.

        Returns
        -------
        str
            The first element of the output.

        Raises
        ------
        RAGTransformationOutputError
            If the list is empty or its first element is not a string.
        """
        if not output:
            raise RAGTransformationOutputError(
                "The transformation model returned an empty output."
            )
        raw = output[0]
        if not isinstance(raw, str):
            raise RAGTransformationOutputError(
                "The transformation model output is not a string: "
                f"{type(raw).__name__}."
            )
        return raw

    @staticmethod
    def _clean_queries(entries: Sequence[Any]) -> List[str]:
        """Coerce, strip, drop empties and deduplicate while preserving order.

        Parameters
        ----------
        entries : Sequence[Any]
            Raw query entries.

        Returns
        -------
        List[str]
            The cleaned queries.
        """
        cleaned: List[str] = []
        for entry in entries:
            if entry is None:
                continue
            text = str(entry).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned

    def _require_list(self, arguments: Dict[str, Any]) -> List[Any]:
        """Validate that the argument key holds a non-empty list.

        Parameters
        ----------
        arguments : Dict[str, Any]
            Parsed arguments mapping.

        Returns
        -------
        List[Any]
            The list of raw query entries.

        Raises
        ------
        RAGTransformationOutputError
            If the key is missing or not a non-empty list.
        """
        entries = arguments.get(self.ARGUMENT_KEY)
        if not isinstance(entries, list) or not entries:
            raise RAGTransformationOutputError(
                f"The model output does not contain a non-empty "
                f"'{self.ARGUMENT_KEY}' list."
            )
        return entries
