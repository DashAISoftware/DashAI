"""Default 1-to-n query decomposition prompt."""

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
    QueryDecompositionPrompt,
)

TEMPLATES = {
    "en": (
        "You are a query decomposition assistant. Split the user's question "
        "into the minimal set of simple, independent sub-queries, each of "
        "which can be used on its own to retrieve relevant documents.\n"
        "\n"
        "Conversation history (may be empty):\n"
        "{history}\n"
        "\n"
        "Current user message:\n"
        "{input}\n"
        "\n"
        "Decide by yourself how many sub-queries are needed and use as few as "
        "possible.\n"
        "Do not produce more than {n_max} sub-queries.\n"
        "Each sub-query must be simple, self-contained and independently "
        "retrievable. Also write a short user-facing message describing what "
        "you did and a short justification explaining why. Do not add any other "
        "explanation.\n"
        "\n"
        "Respond with ONLY one JSON object in this exact OpenAI-style function "
        "call format, with no markdown fences and no extra text:\n"
        '{"name": "decompose_query", "arguments": '
        '{"queries": ["<sub-query 1>", "<sub-query 2>"], '
        '"message": "<one short sentence for the user describing what you did>", '
        '"justification": "<one short sentence explaining why>"}}'
    ),
    "es": (
        "Eres un asistente de descomposición de consultas. Divide la pregunta "
        "del usuario en el conjunto mínimo de subconsultas simples e "
        "independientes, cada una de las cuales pueda usarse por sí sola para "
        "recuperar documentos relevantes.\n"
        "\n"
        "Historial de la conversación (puede estar vacío):\n"
        "{history}\n"
        "\n"
        "Mensaje actual del usuario:\n"
        "{input}\n"
        "\n"
        "Decide por ti mismo cuántas subconsultas hacen falta y usa las "
        "mínimas posibles.\n"
        "No generes más de {n_max} subconsultas.\n"
        "Cada subconsulta debe ser simple, autocontenida e independiente. "
        "Escribe también un mensaje breve para el usuario describiendo lo que "
        "hiciste y una justificación breve de por qué. No añadas ninguna otra "
        "explicación.\n"
        "\n"
        "Responde ÚNICAMENTE con un objeto JSON en este formato exacto de "
        "llamada a función, sin bloques de código ni texto adicional:\n"
        '{"name": "decompose_query", "arguments": '
        '{"queries": ["<subconsulta 1>", "<subconsulta 2>"], '
        '"message": "<una frase breve para el usuario describiendo lo que hiciste>", '
        '"justification": "<una frase breve explicando por qué>"}}'
    ),
    "pt": (
        "Você é um assistente de decomposição de consultas. Divida a pergunta "
        "do usuário no conjunto mínimo de subconsultas simples e "
        "independentes, cada uma das quais possa ser usada por si só para "
        "recuperar documentos relevantes.\n"
        "\n"
        "Histórico da conversa (pode estar vazio):\n"
        "{history}\n"
        "\n"
        "Mensagem atual do usuário:\n"
        "{input}\n"
        "\n"
        "Decida por conta própria quantas subconsultas são necessárias e use "
        "o mínimo possível.\n"
        "Não gere mais de {n_max} subconsultas.\n"
        "Cada subconsulta deve ser simples, autocontida e independente. "
        "Escreva também uma mensagem breve para o usuário descrevendo o que "
        "você fez e uma justificativa breve de por quê. Não adicione nenhuma "
        "outra explicação.\n"
        "\n"
        "Responda APENAS com um objeto JSON neste formato exato de chamada de "
        "função, sem blocos de código e sem texto adicional:\n"
        '{"name": "decompose_query", "arguments": '
        '{"queries": ["<subconsulta 1>", "<subconsulta 2>"], '
        '"message": "<uma frase breve para o usuário descrevendo o que você fez>", '
        '"justification": "<uma frase breve explicando por quê>"}}'
    ),
}


class DefaultQueryDecompositionPromptSchema(BaseSchema):
    """Schema for the default query decomposition prompt.

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


class DefaultQueryDecompositionPrompt(QueryDecompositionPrompt):
    """Default prompt template for decomposing a query into sub-queries."""

    SCHEMA = DefaultQueryDecompositionPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template for decomposing a complex question into"
        " independently retrievable sub-queries.",
        es="Plantilla de prompt predeterminada para descomponer una pregunta"
        " compleja en subconsultas recuperables de forma independiente.",
        pt="Modelo de prompt padrão para decompor uma pergunta complexa em"
        " subconsultas recuperáveis de forma independente.",
        de="Standard-Prompt-Vorlage zum Zerlegen einer komplexen Frage in"
        " unabhängig abrufbare Teilfragen.",
        zh="用于将复杂问题分解为可独立检索子查询的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default Query Decomposition Prompt",
        es="Prompt de Descomposición de Consulta Predeterminado",
        pt="Prompt de Decomposição de Consulta Padrão",
        de="Standard-Abfrage-Zerlegungs-Prompt",
        zh="默认查询分解提示词",
    )

    required_placeholders = ["{input}", "{history}"]
    optional_placeholders = ["{n_max}"]

    metadata = {
        "name": "Default Query Decomposition Prompt",
        "description": "Default prompt template for decomposing a complex question"
        " into independently retrievable sub-queries.",
        "type": "transformation",
        "technique": "decomposition",
        "variant": "default",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to decompose.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
            "{n_max}": (
                "Optional upper bound on the number of sub-queries; the whole "
                "cap sentence disappears when it is not provided."
            ),
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the default decomposition prompt.

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

    def format(
        self,
        input: str,
        history: str,
        n_max: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the decomposition prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        n_max : int | None
            Optional upper bound on the number of sub-queries. When ``None``
            the cap line is removed from the rendered prompt.
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
            {"{n_max}": n_max},
        )
