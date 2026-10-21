"""Default 1-to-1 query rewriting prompt."""

from __future__ import annotations

from typing import Any

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryRewritingPrompt,
)

TEMPLATES = {
    "en": (
        "You are a query rewriting assistant. Rewrite the user message into "
        "exactly one self-contained search query that captures the real "
        "information need, folding in details from the conversation history "
        "only when the new message depends on earlier context.\n"
        "\n"
        "Conversation history (may be empty):\n"
        "{history}\n"
        "\n"
        "Current user message:\n"
        "{input}\n"
        "\n"
        "Write a single, clear, self-contained search query. Use the history "
        "only when needed to resolve references. Also write a short user-facing "
        "message describing what you did and a short justification explaining "
        "why. Do not add any other explanation.\n"
        "\n"
        "Respond with ONLY one JSON object in this exact OpenAI-style function "
        "call format, with no markdown fences and no extra text:\n"
        '{"name": "rewrite_query", "arguments": {"query": "<the rewritten query>", '
        '"message": "<one short sentence for the user describing what you did>", '
        '"justification": "<one short sentence explaining why>"}}'
    ),
    "es": (
        "Eres un asistente de reescritura de consultas. Reescribe el mensaje "
        "del usuario en una única consulta de búsqueda autocontenida que "
        "capture su verdadera necesidad de información, incorporando los "
        "detalles del historial de la conversación solo cuando el nuevo "
        "mensaje dependa del contexto anterior.\n"
        "\n"
        "Historial de la conversación (puede estar vacío):\n"
        "{history}\n"
        "\n"
        "Mensaje actual del usuario:\n"
        "{input}\n"
        "\n"
        "Escribe una sola consulta de búsqueda clara y autocontenida. Usa el "
        "historial solo cuando sea necesario para resolver referencias. Escribe "
        "también un mensaje breve para el usuario describiendo lo que hiciste y "
        "una justificación breve de por qué. No añadas ninguna otra "
        "explicación.\n"
        "\n"
        "Responde ÚNICAMENTE con un objeto JSON en este formato exacto de "
        "llamada a función, sin bloques de código ni texto adicional:\n"
        '{"name": "rewrite_query", "arguments": {"query": "<la consulta reescrita>", '
        '"message": "<una frase breve para el usuario describiendo lo que hiciste>", '
        '"justification": "<una frase breve explicando por qué>"}}'
    ),
    "pt": (
        "Você é um assistente de reescrita de consultas. Reescreva a mensagem "
        "do usuário em uma única consulta de busca autocontida que capture "
        "sua verdadeira necessidade de informação, incorporando os detalhes "
        "do histórico da conversa somente quando a nova mensagem depender do "
        "contexto anterior.\n"
        "\n"
        "Histórico da conversa (pode estar vazio):\n"
        "{history}\n"
        "\n"
        "Mensagem atual do usuário:\n"
        "{input}\n"
        "\n"
        "Escreva uma única consulta de busca clara e autocontida. Use o "
        "histórico somente quando for necessário para resolver referências. "
        "Escreva também uma mensagem breve para o usuário descrevendo o que "
        "você fez e uma justificativa breve de por quê. Não adicione nenhuma "
        "outra explicação.\n"
        "\n"
        "Responda APENAS com um objeto JSON neste formato exato de chamada de "
        "função, sem blocos de código e sem texto adicional:\n"
        '{"name": "rewrite_query", "arguments": {"query": "<a consulta reescrita>", '
        '"message": "<uma frase breve para o usuário descrevendo o que você fez>", '
        '"justification": "<uma frase breve explicando por quê>"}}'
    ),
}


class DefaultQueryRewritingPromptSchema(BaseSchema):
    """Schema for the default query rewriting prompt.

    Attributes:
        language: Language code for the generated instructions (en, es, pt).
        template: The prompt template string with placeholders.
    """

    language: schema_field(
        enum_field(enum=["en", "es", "pt"]),
        placeholder="en",
        description=MultilingualString(
            en="Language for the generated instructions.",
            es="Idioma de las instrucciones generadas.",
            pt="Idioma das instruções geradas.",
            de="Sprache der generierten Anweisungen.",
            zh="生成指令的语言。",
        ),
    )
    template: schema_field(
        string_field(),
        placeholder="",
        description="The prompt template with placeholders.",
    )


class DefaultQueryRewritingPrompt(QueryRewritingPrompt):
    """Default prompt template for rewriting a query into a single search query."""

    SCHEMA = DefaultQueryRewritingPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template for rewriting a query into a single search query.",
        es="Plantilla de prompt predeterminada para reescribir una consulta en"
        " una única consulta de búsqueda.",
        pt="Modelo de prompt padrão para reescrever uma consulta em uma única"
        " consulta de busca.",
        de="Standard-Prompt-Vorlage, um eine Abfrage in eine einzelne"
        " Suchanfrage umzuschreiben.",
        zh="用于将查询改写为单个搜索查询的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default Query Rewriting Prompt",
        es="Prompt de Reescritura de Consulta Predeterminado",
        pt="Prompt de Reescrita de Consulta Padrão",
        de="Standard-Abfrage-Umschreibungs-Prompt",
        zh="默认查询改写提示词",
    )

    required_placeholders = ["{input}", "{history}"]
    optional_placeholders: list[str] = []

    metadata = {
        "name": "Default Query Rewriting Prompt",
        "description": "Default prompt template for rewriting a query into a single"
        " search query.",
        "type": "transformation",
        "technique": "rewriting",
        "variant": "default",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to rewrite.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
            "function_call": (
                "The prompt must answer with the function call "
                '{"name": "rewrite_query", "arguments": {"query": "..."}}.'
            ),
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the default rewriting prompt.

        Parameters
        ----------
        language : str
            Language code used to pick the default template ("en", "es", "pt").
        template : str, optional
            Override template. When omitted, the template for ``language`` is
            used.

        Raises
        ------
        RAGPromptTemplateError
            If no template is available for the language or the resolved
            template is missing required placeholders.
        """
        self.language = kwargs.pop("language")
        if "template" in kwargs:
            self.template = kwargs.pop("template")
        else:
            self.template = TEMPLATES.get(self.language, "")
        if not self.template:
            raise RAGPromptTemplateError(
                f"No template available for language: {self.language}"
            )
        self._validate()

    def format(self, input: str, history: str, **kwargs: Any) -> str:
        """Render the rewriting prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        **kwargs
            Unused.

        Returns
        -------
        str
            The rendered prompt.

        Raises
        ------
        RAGPromptTemplateError
            If the template is missing required placeholders.
        """
        self._validate()
        return self._render(
            self.template,
            {"{input}": input, "{history}": history},
        )
