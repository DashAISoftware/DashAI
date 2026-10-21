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
        "Documents: {documents.names}\n"
        "\n"
        "Document description: {documents.description}\n"
        "\n"
        "Retrieved chunks (each line shows its document_id and position):\n"
        "{chunks}\n"
        "\n"
        "Candidate pool size: {pool_size} chunks.\n"
        "\n"
        "Maximum retrievable chunks: {topk}.\n"
        "\n"
        "Retriever catalog: {retriever.description}\n"
        "\n"
        "Respond by calling the function evaluate_retrieval_sufficiency with a "
        "single JSON object with this shape:\n"
        '{"sufficient": <true or false>, "call_retrievers": '
        '{"<retriever index>": <top_k>}, "request_chunks": '
        '{"<document id>": [<chunk positions>]}, "discard": '
        '{"<document id>": [<chunk positions>]}, '
        '"message": "<one short user-facing sentence>", '
        '"justification": "<one short rationale>"}\n'
        "\n"
        '- "sufficient" is required and says whether the retrieved chunks '
        "answer the user message.\n"
        '- "message" is optional: one short user-facing sentence in the same '
        "language as this prompt describing what you decided to do.\n"
        '- "justification" is optional: one short sentence in the same '
        "language as this prompt explaining why.\n"
        '- "call_retrievers" maps 1-based retriever indices from the retriever '
        "catalog to the number of chunks to retrieve from that retriever next. "
        "Indices must be at least 1.\n"
        '- "request_chunks" maps document ids to chunk positions (taken from '
        "the retrieved chunk lines) to include in the pool, even if no "
        "retriever returned them.\n"
        '- "discard" maps document ids to chunk positions (taken from the '
        "retrieved chunk lines) to exclude from the pool.\n"
        "- Requests and discards persist across rounds and can override each "
        "other: the last action applied to a chunk wins.\n"
        '- When "sufficient" is true, omit "call_retrievers", '
        '"request_chunks" and "discard".\n'
        "- An insufficient verdict must request at least one retriever, chunk "
        "or discard.\n"
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
        "Documentos: {documents.names}\n"
        "\n"
        "Descripción de los documentos: {documents.description}\n"
        "\n"
        "Fragmentos recuperados (cada línea muestra su document_id y posición):\n"
        "{chunks}\n"
        "\n"
        "Tamaño del conjunto de candidatos: {pool_size} fragmentos.\n"
        "\n"
        "Máximo de fragmentos recuperables: {topk}.\n"
        "\n"
        "Catálogo de recuperadores: {retriever.description}\n"
        "\n"
        "Responde llamando a la función evaluate_retrieval_sufficiency con un "
        "único objeto JSON con esta forma:\n"
        '{"sufficient": <true o false>, "call_retrievers": '
        '{"<índice del recuperador>": <top_k>}, "request_chunks": '
        '{"<id del documento>": [<posiciones de fragmentos>]}, "discard": '
        '{"<id del documento>": [<posiciones de fragmentos>]}, '
        '"message": "<una frase breve para el usuario>", '
        '"justification": "<una justificación breve>"}\n'
        "\n"
        '- "sufficient" es obligatorio e indica si los fragmentos recuperados '
        "responden al mensaje del usuario.\n"
        '- "message" es opcional: una frase breve para el usuario, en el mismo '
        "idioma de este prompt, describiendo lo que decidiste hacer.\n"
        '- "justification" es opcional: una frase breve, en el mismo idioma de '
        "este prompt, explicando por qué.\n"
        '- "call_retrievers" asigna índices de recuperador basados en 1 del '
        "catálogo al número de fragmentos a recuperar de ese recuperador en la "
        "siguiente ronda. Los índices deben ser al menos 1.\n"
        '- "request_chunks" asigna ids de documento a posiciones de fragmento '
        "(tomadas de las líneas de fragmentos recuperados) que se incluirán en "
        "el conjunto, aunque ningún recuperador las haya devuelto.\n"
        '- "discard" asigna ids de documento a posiciones de fragmento (tomadas '
        "de las líneas de fragmentos recuperados) que se excluirán del "
        "conjunto.\n"
        "- Las solicitudes y descartes persisten entre rondas y pueden "
        "sobrescribirse: la última acción aplicada a un fragmento prevalece.\n"
        '- Cuando "sufficient" sea true, omite "call_retrievers", '
        '"request_chunks" y "discard".\n'
        "- Un veredicto insuficiente debe solicitar al menos un recuperador, "
        "fragmento o descarte.\n"
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
        "Documentos: {documents.names}\n"
        "\n"
        "Descrição dos documentos: {documents.description}\n"
        "\n"
        "Trechos recuperados (cada linha mostra seu document_id e posição):\n"
        "{chunks}\n"
        "\n"
        "Tamanho do conjunto de candidatos: {pool_size} trechos.\n"
        "\n"
        "Máximo de trechos recuperáveis: {topk}.\n"
        "\n"
        "Catálogo de recuperadores: {retriever.description}\n"
        "\n"
        "Responda chamando a função evaluate_retrieval_sufficiency com um "
        "único objeto JSON com esta forma:\n"
        '{"sufficient": <true ou false>, "call_retrievers": '
        '{"<índice do recuperador>": <top_k>}, "request_chunks": '
        '{"<id do documento>": [<posições de trechos>]}, "discard": '
        '{"<id do documento>": [<posições de trechos>]}, '
        '"message": "<uma frase breve para o usuário>", '
        '"justification": "<uma justificativa breve>"}\n'
        "\n"
        '- "sufficient" é obrigatório e indica se os trechos recuperados '
        "respondem à mensagem do usuário.\n"
        '- "message" é opcional: uma frase breve para o usuário, no mesmo '
        "idioma deste prompt, descrevendo o que você decidiu fazer.\n"
        '- "justification" é opcional: uma frase breve, no mesmo idioma deste '
        "prompt, explicando por quê.\n"
        '- "call_retrievers" mapeia índices de recuperador baseados em 1 do '
        "catálogo para o número de trechos a recuperar desse recuperador na "
        "próxima rodada. Os índices devem ser pelo menos 1.\n"
        '- "request_chunks" mapeia ids de documento para posições de trecho '
        "(obtidas das linhas de trechos recuperados) a incluir no conjunto, "
        "mesmo que nenhum recuperador as tenha retornado.\n"
        '- "discard" mapeia ids de documento para posições de trecho (obtidas '
        "das linhas de trechos recuperados) a excluir do conjunto.\n"
        "- Solicitações e descartes persistem entre rodadas e podem ser "
        "sobrescritos: a última ação aplicada a um trecho prevalece.\n"
        '- Quando "sufficient" for true, omita "call_retrievers", '
        '"request_chunks" e "discard".\n'
        "- Um veredicto insuficiente deve solicitar pelo menos um recuperador, "
        "trecho ou descarte.\n"
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

    required_placeholders = RetrievalSufficiencyPrompt.required_placeholders
    optional_placeholders = RetrievalSufficiencyPrompt.optional_placeholders

    metadata = {
        "name": "Default Retrieval Sufficiency Prompt",
        "description": "Default prompt template for deciding whether retrieved"
        " chunks are sufficient and which retrievers or chunks to fetch next.",
        "type": "evaluation",
        "technique": "sufficiency",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message the chunks must answer.",
            "{chunks}": (
                "The chunks under evaluation, one line per chunk carrying its "
                "document_id, position and text; a preformatted string is kept "
                "verbatim."
            ),
            "{children_catalog}": (
                "Optional alias for the retriever catalog; the whole line "
                "disappears when it is not provided."
            ),
            "{pool_size}": (
                "Optional candidate pool size; the whole line disappears when "
                "it is not provided."
            ),
            "{topk}": (
                "Optional maximum number of retrievable chunks; the whole line "
                "disappears when it is not provided."
            ),
            "{retriever.description}": (
                "Optional JSON catalog of the retrievers; the whole line "
                "disappears when it is not provided."
            ),
            "{documents.names}": (
                "Optional comma-separated document names; the whole line "
                "disappears when it is not provided."
            ),
            "{documents.description}": (
                "Optional JSON document summary; the whole line disappears when "
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
