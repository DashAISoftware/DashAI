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
from DashAI.back.models.RAG.progress_utils import (
    normalize_progress_text,
    report_progress,
    sanitize_text,
)
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryTransformationPrompt,
)
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PROGRESS_JUSTIFICATION_KEY,
    RAG_PROGRESS_MESSAGE_KEY,
    RAG_PROGRESS_STAGE_TRANSFORMING,
)
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_FUNCTION_CALL_MAX_TRIALS,
    MAX_FUNCTION_CALL_TRIALS,
)
from DashAI.back.models.RAG.transformation.base_query_transformation import (
    BaseQueryTransformation,
    QueryTransformationResult,
)
from DashAI.back.models.RAG.transformation.llm_output_parser import (
    parse_function_call_output,
    resolve_arguments_dict,
    truncate_preview,
)
from DashAI.back.models.text_to_text_generation_model import FunctionCallResult

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
        function_call_max_trials: Maximum number of function-call attempts,
            the first call included.
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
        placeholder={"component": "Qwen25_15BInstruct", "params": {}},
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
        alias=MultilingualString(
            en="History window",
            es="Ventana de historial",
            pt="Janela de histórico",
            de="Verlaufsfenster",
            zh="历史窗口",
        ),
    )
    # Intentional Pydantic default: persisted session configs created before
    # this parameter existed must keep validating on the job path. The
    # placeholder still drives UI and new-session default resolution.
    function_call_max_trials: schema_field(
        int_field(ge=1, le=MAX_FUNCTION_CALL_TRIALS, strict=True),
        placeholder=DEFAULT_FUNCTION_CALL_MAX_TRIALS,
        description=MultilingualString(
            en="Maximum number of function-call attempts, including the first."
            " When the model returns an unusable call or unparseable JSON"
            " arguments, the call is retried until this limit is reached."
            " Only applies to models with function calling.",
            es="Número máximo de intentos de llamada a funciones, incluido el"
            " primero. Cuando el modelo devuelve una llamada inutilizable o"
            " argumentos JSON no analizables, la llamada se reintenta hasta"
            " alcanzar este límite. Solo se aplica a modelos con llamada a"
            " funciones.",
            pt="Número máximo de tentativas de chamada de função, incluindo a"
            " primeira. Quando o modelo retorna uma chamada inutilizável ou"
            " argumentos JSON não analisáveis, a chamada é repetida até atingir"
            " esse limite. Aplica-se apenas a modelos com chamada de função.",
            de="Maximale Anzahl von Funktionsaufrufversuchen, einschließlich des"
            " ersten. Wenn das Modell einen unbrauchbaren Aufruf oder nicht"
            " analysierbare JSON-Argumente liefert, wird der Aufruf bis zu"
            " diesem Limit wiederholt. Gilt nur für Modelle mit"
            " Funktionsaufrufen.",
            zh="函数调用尝试的最大次数，包括首次调用。当模型返回不可用的调用"
            "或无法解析的 JSON 参数时，会重试调用直到达到此限制。仅适用于"
            "支持函数调用的模型。",
        ),
        alias=MultilingualString(
            en="Function call max trials",
            es="Máximo de intentos de llamada a funciones",
            pt="Máximo de tentativas de chamada de função",
            de="Max. Funktionsaufrufversuche",
            zh="函数调用最大尝试次数",
        ),
    ) = DEFAULT_FUNCTION_CALL_MAX_TRIALS  # type: ignore


class LLMQueryTransformation(BaseQueryTransformation):
    """Shared implementation for the LLM-backed transformers.

    Subclasses set ``EXPECTED_FUNCTION`` and ``ARGUMENT_KEY``, implement
    ``_render_prompt`` (to call the technique's prompt) and ``_parse_arguments``
    (to validate the parsed arguments mapping).

    When the configured model reports function-calling support
    (:meth:`TextToTextGenerationTaskModel.supports_function_calling`), the base
    routes through :meth:`generate_function_call` with the technique's
    ``FUNCTION_DESCRIPTION``/``FUNCTION_PARAMETERS`` so constrained sampling
    makes the output shape deterministic. Otherwise it falls back to the
    prompt-obedience text route parsed by the tolerant output parser.
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
    #: Whether bare top-level JSON arrays are tolerated by the text route.
    TOLERATE_BARE_LISTS: bool = False
    #: Description of the function exposed to function-calling backends.
    FUNCTION_DESCRIPTION: str = ""
    #: JSON schema (``type``/``properties``/``required``) of the technique's
    #: function arguments for function-calling backends.
    FUNCTION_PARAMETERS: ClassVar[Dict[str, Any]] = {}

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
        function_call_max_trials : int, optional
            Maximum number of function-call attempts, the first call included.
            Defaults to :data:`DEFAULT_FUNCTION_CALL_MAX_TRIALS`.

        Raises
        ------
        RAGTransformationConfigError
            If ``prompt`` or ``llm_model`` is missing, or
            ``function_call_max_trials`` is not a positive integer.
        """
        self.prompt = kwargs.pop("prompt", None)
        self.llm_model = kwargs.pop("llm_model", None)
        self.history_window = kwargs.pop("history_window", 2)
        self.function_call_max_trials = kwargs.pop(
            "function_call_max_trials", DEFAULT_FUNCTION_CALL_MAX_TRIALS
        )
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
        if (
            isinstance(self.function_call_max_trials, bool)
            or not isinstance(self.function_call_max_trials, int)
            or not 1 <= self.function_call_max_trials <= MAX_FUNCTION_CALL_TRIALS
        ):
            raise RAGTransformationConfigError(
                "'function_call_max_trials' must be an integer between 1 and "
                f"{MAX_FUNCTION_CALL_TRIALS}, got {self.function_call_max_trials!r}."
            )

    def close(self) -> None:
        """Release the transformation LLM, when it exposes a ``close`` hook.

        A failure while closing the model is suppressed so cleanup never masks
        the transformation failure that ended the stage. The call is idempotent
        when the model is a :class:`~DashAI.back.models.lazy_llm.LazyLLM`.

        Returns
        -------
        None
            Nothing.
        """
        close = getattr(self.llm_model, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.warning(
                    "Error closing %s's transformation LLM.",
                    type(self).__name__,
                    exc_info=True,
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
            The cleaned, deduplicated queries plus the optional user-facing
            narrative the model supplied alongside them.

        Raises
        ------
        RAGTransformationConfigError
            If the function-calling route is selected but misconfigured, or the
            prompt/model prerequisites are missing.
        RAGTransformationOutputError
            If the model produced no usable output or the function-calling
            backend failed to emit a call.
        """
        history_block = format_history(history, self.history_window)
        arguments = self._obtain_arguments(message, history_block)
        parsed = self._parse_arguments(arguments)
        cleaned = self._clean_queries(parsed)
        progress_message = normalize_progress_text(
            arguments.get(RAG_PROGRESS_MESSAGE_KEY)
        )
        progress_justification = normalize_progress_text(
            arguments.get(RAG_PROGRESS_JUSTIFICATION_KEY)
        )
        final_queries = self._finalize_queries(cleaned)
        if progress_message or progress_justification:
            report_progress(
                RAG_PROGRESS_STAGE_TRANSFORMING,
                message=progress_message,
                justification=progress_justification,
            )
        return QueryTransformationResult(
            queries=final_queries,
            message=progress_message,
            justification=progress_justification,
        )

    def _obtain_arguments(self, message: str, history_block: str) -> Dict[str, Any]:
        """Get the technique's raw arguments mapping from the model.

        The technique prompt is rendered once and sent verbatim on both routes.
        When the model supports function calling, the prompt is paired with the
        technique's function schema (the format contract it also contains is
        harmless under forced tool choice); otherwise the prompt is answered as
        text and parsed by the tolerant output parser.

        Parameters
        ----------
        message : str
            The current user message.
        history_block : str
            The already-formatted conversation history block.

        Returns
        -------
        Dict[str, Any]
            The raw arguments mapping emitted by the model.

        Raises
        ------
        RAGTransformationOutputError
            If the text route produced no usable function-call output.
        RAGTransformationConfigError
            If the function-calling route is selected but misconfigured.
        """
        prompt_text = self._render_prompt(message, history_block)
        if self.llm_model.supports_function_calling():
            return self._call_function_calling(prompt_text)
        raw = self._extract_raw_output(
            self.llm_model.generate([{"role": "user", "content": prompt_text}])
        )
        if self.TOLERATE_BARE_LISTS:
            list_argument_key: str | None = self.ARGUMENT_KEY
        else:
            list_argument_key = None
        return parse_function_call_output(
            raw,
            self.EXPECTED_FUNCTION,
            self.ARGUMENT_KEY,
            list_argument_key=list_argument_key,
        )

    def _call_function_calling(self, prompt_text: str) -> Dict[str, Any]:
        """Call the LLM with the technique's function schema (function calling).

        Parameters
        ----------
        prompt_text : str
            The rendered technique prompt sent as the user message.

        Returns
        -------
        Dict[str, Any]
            The validated arguments mapping emitted for the technique's
            function.

        Raises
        ------
        RAGTransformationConfigError
            If the technique declares no function spec, or the model reports
            function-calling support without implementing it.
        RAGTransformationOutputError
            If the backend failed to emit a call, the model did not call the
            expected function, or it returned arguments that are not a JSON
            object. Retried up to ``function_call_max_trials`` attempts; the
            last error is raised once the attempts are exhausted.
        """
        spec = self._function_call_spec()
        messages = [{"role": "user", "content": prompt_text}]
        for attempt in range(1, self.function_call_max_trials):
            try:
                return self._attempt_function_call(messages, spec)
            except RAGTransformationOutputError as err:
                logger.warning(
                    "Function-calling attempt %d of %d failed for %s; retrying: %s",
                    attempt,
                    self.function_call_max_trials,
                    type(self).__name__,
                    err,
                )
        return self._attempt_function_call(messages, spec)

    def _function_call_spec(self) -> Dict[str, Any]:
        """Return the function spec exposed to the function-calling backend.

        Returns
        -------
        Dict[str, Any]
            The ``name``/``description``/``parameters`` specification.

        Raises
        ------
        RAGTransformationConfigError
            If the technique declares no function spec.
        """
        if not self.FUNCTION_DESCRIPTION or not self.FUNCTION_PARAMETERS:
            raise RAGTransformationConfigError(
                f"{type(self).__name__} does not declare a function spec to use "
                "function calling; declare FUNCTION_DESCRIPTION and "
                "FUNCTION_PARAMETERS or use a text route."
            )
        return {
            "name": self.EXPECTED_FUNCTION,
            "description": self.FUNCTION_DESCRIPTION,
            "parameters": self.FUNCTION_PARAMETERS,
        }

    def _attempt_function_call(
        self, messages: List[Dict[str, str]], spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform one function-call attempt and validate its result.

        Parameters
        ----------
        messages : List[Dict[str, str]]
            The chat messages sent verbatim on every attempt.
        spec : Dict[str, Any]
            The technique's function specification.

        Returns
        -------
        Dict[str, Any]
            The validated arguments mapping.

        Raises
        ------
        RAGTransformationConfigError
            If the model reports support but implements no function-calling
            method.
        RAGTransformationOutputError
            If the backend failed or returned an unusable call.
        """
        try:
            result = self.llm_model.generate_function_call(
                messages=messages,
                functions=[spec],
            )
        except NotImplementedError as err:
            raise RAGTransformationConfigError(
                "The transformation LLM reports function calling support but does "
                "not implement generate_function_call."
            ) from err
        except Exception as err:
            # Normalize every backend failure (RuntimeError/ValueError raised by
            # the base implementations, or unexpected KeyError/TypeError from a
            # drifted backend) so RAG_pipeline's RAGTransformationError handling
            # degrades the chat turn gracefully.
            raise RAGTransformationOutputError(
                f"Function calling failed: {err}"
            ) from err
        return self._validate_function_call_result(result)

    def _validate_function_call_result(self, result: Any) -> Dict[str, Any]:
        """Validate the model's function-call response and resolve arguments.

        Parameters
        ----------
        result : Any
            The raw return value of ``generate_function_call``.

        Returns
        -------
        Dict[str, Any]
            The arguments mapping, with a JSON-encoded string resolved to a
            dict when necessary.

        Raises
        ------
        RAGTransformationOutputError
            If the result is not a :class:`FunctionCallResult`, it did not call
            the expected function, or its arguments are not a JSON object.
        """
        if not isinstance(result, FunctionCallResult):
            raise RAGTransformationOutputError(
                "The function-calling model returned an unexpected output shape: "
                f"{type(result).__name__}."
            )
        called_name = result.name
        if not called_name:
            raise RAGTransformationOutputError(
                "The function-calling model did not report a function name."
            )
        if called_name != self.EXPECTED_FUNCTION:
            raise RAGTransformationOutputError(
                f"The model called '{called_name}' instead of the expected "
                f"'{self.EXPECTED_FUNCTION}'."
            )
        arguments = resolve_arguments_dict(result.arguments)
        if arguments is None:
            raise RAGTransformationOutputError(
                "The function-calling model did not return a JSON object for "
                f"'{self.EXPECTED_FUNCTION}' arguments. "
                f"Preview: {truncate_preview(result.arguments)}"
            )
        return arguments

    def _render_prompt(self, message: str, history_block: str) -> str:
        """Render the technique prompt. Implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")

    def _parse_arguments(self, arguments: Dict[str, Any]) -> List[str]:
        """Parse and validate the model arguments. Implemented by subclasses.

        Concrete techniques override this to validate the shape of
        ``arguments`` (identified by :attr:`ARGUMENT_KEY`) and return the raw
        query entries as strings.
        """
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
            text = sanitize_text(str(entry)).strip()
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
