"""Default retrieval sufficiency evaluation prompt."""

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
from DashAI.back.models.RAG.prompts.evaluation.retrieval_sufficiency_prompt import (
    RetrievalSufficiencyPrompt,
)

TEMPLATES = {
    "en": (
        "You are a retrieval sufficiency evaluator for a Retrieval-Augmented "
        "Generation system. Decide whether the retrieved chunks are enough to "
        "answer the user message.\n"
        "\n"
        "User message:\n"
        "{input}\n"
        "\n"
        "Retrieved chunks:\n"
        "{chunks}\n"
        "\n"
        'Child retriever catalog, as "index: retriever name": '
        "{children_catalog}\n"
        "\n"
        "Candidate pool size: {pool_size} chunks.\n"
        "\n"
        "If the chunks are sufficient, respond with "
        '{"sufficient": true}.\n'
        "If more chunks are needed from the same retrievers, respond with "
        '{"sufficient": false, "top_k": <positive integer>}, using the '
        "suggested chunk count for the next retrieval round.\n"
        "To consult specific child retrievers, respond with "
        '{"sufficient": false, "children": [<indices selected from: '
        "{children_catalog}>]}.\n"
        "When the retrieved chunks are absent or empty, decide which "
        "retrievers to consult.\n"
        'When no child retriever catalog is available, the "children" field '
        "must not appear.\n"
        "\n"
        "Respond with ONLY one JSON object, with no markdown fences and no "
        "extra text."
    ),
    "es": (
        "Eres un evaluador de suficiencia de recuperación para un sistema de "
        "Generación Aumentada por Recuperación. Decide si los fragmentos "
        "recuperados son suficientes para responder al mensaje del usuario.\n"
        "\n"
        "Mensaje del usuario:\n"
        "{input}\n"
        "\n"
        "Fragmentos recuperados:\n"
        "{chunks}\n"
        "\n"
        'Catálogo de recuperadores hijos, como "índice: nombre del '
        'recuperador": {children_catalog}\n'
        "\n"
        "Tamaño del conjunto de candidatos: {pool_size} fragmentos.\n"
        "\n"
        "Si los fragmentos son suficientes, responde con "
        '{"sufficient": true}.\n'
        "Si necesitas más fragmentos de los mismos recuperadores, responde con "
        '{"sufficient": false, "top_k": <entero positivo>}, usando la cantidad '
        "sugerida de fragmentos para la siguiente ronda de recuperación.\n"
        "Para consultar recuperadores hijos específicos, responde con "
        '{"sufficient": false, "children": [<índices seleccionados de: '
        "{children_catalog}>]}.\n"
        "Cuando los fragmentos recuperados estén ausentes o vacíos, decide qué "
        "recuperadores consultar.\n"
        "Cuando no haya un catálogo de recuperadores hijos disponible, el "
        'campo "children" no debe aparecer.\n'
        "\n"
        "Responde ÚNICAMENTE con un objeto JSON, sin bloques de código ni "
        "texto adicional."
    ),
    "pt": (
        "Você é um avaliador de suficiência de recuperação para um sistema de "
        "Geração Aumentada por Recuperação. Decida se os trechos recuperados "
        "são suficientes para responder à mensagem do usuário.\n"
        "\n"
        "Mensagem do usuário:\n"
        "{input}\n"
        "\n"
        "Trechos recuperados:\n"
        "{chunks}\n"
        "\n"
        'Catálogo de recuperadores filhos, como "índice: nome do '
        'recuperador": {children_catalog}\n'
        "\n"
        "Tamanho do conjunto de candidatos: {pool_size} trechos.\n"
        "\n"
        "Se os trechos forem suficientes, responda com "
        '{"sufficient": true}.\n'
        "Se precisar de mais trechos dos mesmos recuperadores, responda com "
        '{"sufficient": false, "top_k": <inteiro positivo>}, usando a '
        "quantidade sugerida de trechos para a próxima rodada de recuperação.\n"
        "Para consultar recuperadores filhos específicos, responda com "
        '{"sufficient": false, "children": [<índices selecionados de: '
        "{children_catalog}>]}.\n"
        "Quando os trechos recuperados estiverem ausentes ou vazios, decida "
        "quais recuperadores consultar.\n"
        "Quando não houver um catálogo de recuperadores filhos disponível, o "
        'campo "children" não deve aparecer.\n'
        "\n"
        "Responda APENAS com um objeto JSON, sem blocos de código e sem texto "
        "adicional."
    ),
}


class DefaultRetrievalSufficiencyPromptSchema(BaseSchema):
    """Schema for the default retrieval sufficiency prompt.

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


class DefaultRetrievalSufficiencyPrompt(RetrievalSufficiencyPrompt):
    """Default prompt template for judging retrieval sufficiency."""

    SCHEMA = DefaultRetrievalSufficiencyPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template for deciding whether retrieved chunks are"
        " sufficient and which retrievers to consult next.",
        es="Plantilla de prompt predeterminada para decidir si los fragmentos"
        " recuperados son suficientes y qué recuperadores consultar después.",
        pt="Modelo de prompt padrão para decidir se os trechos recuperados são"
        " suficientes e quais recuperadores consultar em seguida.",
        de="Standard-Prompt-Vorlage, um zu entscheiden, ob abgerufene Fragmente"
        " ausreichen und welche Retriever als Nächstes zu konsultieren sind.",
        zh="用于判断已检索片段是否充分以及下一步咨询哪些检索器的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default Retrieval Sufficiency Prompt",
        es="Prompt de Suficiencia de Recuperación Predeterminado",
        pt="Prompt de Suficiência de Recuperação Padrão",
        de="Standard-Retrieval-Suffizienz-Prompt",
        zh="默认检索充分性提示词",
    )

    required_placeholders = ["{input}", "{chunks}"]
    optional_placeholders = ["{children_catalog}", "{pool_size}"]

    metadata = {
        "name": "Default Retrieval Sufficiency Prompt",
        "description": "Default prompt template for deciding whether retrieved"
        " chunks are sufficient and which retrievers to consult next.",
        "type": "evaluation",
        "technique": "sufficiency",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message the chunks must answer.",
            "{chunks}": (
                "The already-retrieved chunks under evaluation; empty when the "
                "previous round returned nothing."
            ),
            "{children_catalog}": (
                "Optional child-retriever catalog; the whole line disappears "
                "when it is not provided."
            ),
            "{pool_size}": (
                "Optional candidate pool size; the whole line disappears when "
                "it is not provided."
            ),
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the default sufficiency prompt.

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
        chunks: str,
        children_catalog: str | None = None,
        pool_size: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the default sufficiency prompt.

        Parameters
        ----------
        input : str
            The current user message.
        chunks : str
            The already-formatted block of retrieved chunks.
        children_catalog : str | None
            Optional child-retriever catalog. When ``None`` the owning line is
            removed from the rendered prompt.
        pool_size : int | None
            Optional candidate pool size. When ``None`` the owning line is
            removed from the rendered prompt.
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
            {"{input}": input, "{chunks}": chunks},
            {"{children_catalog}": children_catalog, "{pool_size}": pool_size},
        )
