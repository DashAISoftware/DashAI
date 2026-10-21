"""Default 1-to-n query expansion prompt."""

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
    QueryExpansionPrompt,
)

TEMPLATES = {
    "en": (
        "You are a query expansion assistant. Rewrite the user message into "
        "exactly {n} search queries that broaden retrieval coverage so that "
        "more relevant documents can be found.\n"
        "\n"
        "Conversation history (may be empty):\n"
        "{history}\n"
        "\n"
        "Current user message:\n"
        "{input}\n"
        "\n"
        "Produce exactly {n} concise, independent search queries or keyword "
        "phrases. At least one of them must closely preserve the original "
        "request; the others should cover related terms, synonyms or angles "
        "that may appear in relevant documents. Also write a short user-facing "
        "message describing what you did and a short justification explaining "
        "why. Do not add any other explanation.\n"
        "\n"
        "Respond with ONLY one JSON object in this exact OpenAI-style function "
        "call format, with no markdown fences and no extra text:\n"
        '{"name": "expand_query", "arguments": {"queries": ["<query 1>", '
        '"<query 2>"], "message": "<one short sentence for the user describing '
        'what you did>", "justification": "<one short sentence explaining why>"}}'
    ),
    "es": (
        "Eres un asistente de expansión de consultas. Reescribe el mensaje "
        "del usuario en exactamente {n} consultas de búsqueda que amplíen la "
        "cobertura de recuperación para encontrar más documentos "
        "relevantes.\n"
        "\n"
        "Historial de la conversación (puede estar vacío):\n"
        "{history}\n"
        "\n"
        "Mensaje actual del usuario:\n"
        "{input}\n"
        "\n"
        "Genera exactamente {n} consultas de búsqueda o frases clave "
        "concisas e independientes. Al menos una debe conservar fielmente la "
        "petición original; las demás deben cubrir términos, sinónimos o "
        "enfoques relacionados que puedan aparecer en documentos relevantes. "
        "Escribe también un mensaje breve para el usuario describiendo lo que "
        "hiciste y una justificación breve de por qué. No añadas ninguna otra "
        "explicación.\n"
        "\n"
        "Responde ÚNICAMENTE con un objeto JSON en este formato exacto de "
        "llamada a función, sin bloques de código ni texto adicional:\n"
        '{"name": "expand_query", "arguments": '
        '{"queries": ["<consulta 1>", "<consulta 2>"], '
        '"message": "<una frase breve para el usuario describiendo lo que hiciste>", '
        '"justification": "<una frase breve explicando por qué>"}}'
    ),
    "pt": (
        "Você é um assistente de expansão de consultas. Reescreva a mensagem "
        "do usuário em exatamente {n} consultas de busca que ampliem a "
        "cobertura de recuperação para encontrar mais documentos "
        "relevantes.\n"
        "\n"
        "Histórico da conversa (pode estar vazio):\n"
        "{history}\n"
        "\n"
        "Mensagem atual do usuário:\n"
        "{input}\n"
        "\n"
        "Gere exatamente {n} consultas de busca ou frases-chave concisas e "
        "independentes. Pelo menos uma deve preservar fielmente a solicitação "
        "original; as demais devem cobrir termos, sinônimos ou ângulos "
        "relacionados que possam aparecer em documentos relevantes. Escreva "
        "também uma mensagem breve para o usuário descrevendo o que você fez e "
        "uma justificativa breve de por quê. Não adicione nenhuma outra "
        "explicação.\n"
        "\n"
        "Responda APENAS com um objeto JSON neste formato exato de chamada de "
        "função, sem blocos de código e sem texto adicional:\n"
        '{"name": "expand_query", "arguments": '
        '{"queries": ["<consulta 1>", "<consulta 2>"], '
        '"message": "<uma frase breve para o usuário descrevendo o que você fez>", '
        '"justification": "<uma frase breve explicando por quê>"}}'
    ),
}


class DefaultQueryExpansionPromptSchema(BaseSchema):
    """Schema for the default query expansion prompt.

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


class DefaultQueryExpansionPrompt(QueryExpansionPrompt):
    """Default prompt template for expanding a query into several queries."""

    SCHEMA = DefaultQueryExpansionPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template for expanding a query into several search queries.",
        es="Plantilla de prompt predeterminada para expandir una consulta en"
        " varias consultas de búsqueda.",
        pt="Modelo de prompt padrão para expandir uma consulta em várias"
        " consultas de busca.",
        de="Standard-Prompt-Vorlage, um eine Abfrage in mehrere Suchanfragen"
        " zu erweitern.",
        zh="用于将查询扩展为多个搜索查询的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default Query Expansion Prompt",
        es="Prompt de Expansión de Consulta Predeterminado",
        pt="Prompt de Expansão de Consulta Padrão",
        de="Standard-Abfrage-Erweiterungs-Prompt",
        zh="默认查询扩展提示词",
    )

    required_placeholders = ["{input}", "{history}", "{n}"]
    optional_placeholders: list[str] = []

    metadata = {
        "name": "Default Query Expansion Prompt",
        "description": "Default prompt template for expanding a query into several"
        " search queries.",
        "type": "transformation",
        "technique": "expansion",
        "variant": "default",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to expand.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
            "{n}": "The exact number of queries the model must produce.",
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the default expansion prompt.

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

    def format(self, input: str, history: str, n: int, **kwargs: Any) -> str:
        """Render the expansion prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        n : int
            Number of queries the model must produce.
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
            {"{input}": input, "{history}": history, "{n}": n},
        )
