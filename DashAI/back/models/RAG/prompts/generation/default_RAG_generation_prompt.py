from typing import Any, Optional

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.generation.RAG_generation_prompt import (
    RAGGenerationPrompt,
)

TEMPLATES = {
    "en": (
        "You are a helpful AI assistant with access to a set of retrieved "
        "documents.\n"
        "Use the documents below to support your answer. Prioritize "
        "information from the documents over your own knowledge. "
        "If the documents do not contain relevant information, say so "
        "clearly rather than guessing.\n"
        "\n"
        "User message:\n"
        "{input}\n"
        "Search queries used for retrieval: {queries}\n"
        "\n"
        "Retrieved documents:\n"
        "{chunks}\n"
        "\n"
        "Answer the user's message based on the documents above."
    ),
    "es": (
        "Eres un asistente de IA con acceso a un conjunto de documentos "
        "recuperados.\n"
        "Usa los documentos a continuación para fundamentar tu respuesta. "
        "Prioriza la información de los documentos sobre tu propio "
        "conocimiento. Si los documentos no contienen información relevante, "
        "indícalo claramente en lugar de adivinar.\n"
        "\n"
        "Mensaje del usuario:\n"
        "{input}\n"
        "Consultas de búsqueda utilizadas para recuperar: {queries}\n"
        "\n"
        "Documentos recuperados:\n"
        "{chunks}\n"
        "\n"
        "Responde al mensaje del usuario basándote en los documentos "
        "anteriores."
    ),
    "pt": (
        "Você é um assistente de IA com acesso a um conjunto de documentos "
        "recuperados.\n"
        "Use os documentos abaixo para fundamentar sua resposta. Priorize "
        "as informações dos documentos sobre seu próprio conhecimento. Se "
        "os documentos não contiverem informações relevantes, indique isso "
        "claramente em vez de adivinhar.\n"
        "\n"
        "Mensagem do usuário:\n"
        "{input}\n"
        "Consultas de pesquisa utilizadas para recuperar: {queries}\n"
        "\n"
        "Documentos recuperados:\n"
        "{chunks}\n"
        "\n"
        "Responda à mensagem do usuário com base nos documentos acima."
    ),
}


class DefaultRAGGenerationPromptSchema(BaseSchema):
    """Schema for the default RAG generation prompt.

    Attributes:
        language: Language code for the response (en, es, pt).
        template: The prompt template string with placeholders.
    """

    language: schema_field(
        enum_field(enum=["en", "es", "pt"]),
        placeholder="en",
        description=MultilingualString(
            en="Language for the generated response.",
            es="Idioma de la respuesta generada.",
            pt="Idioma da resposta gerada.",
            de="Sprache der generierten Antwort.",
            zh="生成回复的语言。",
        ),
    )
    template: schema_field(
        string_field(),
        placeholder="",
        description="The prompt template with placeholders.",
    )


class DefaultRAGGenerationPrompt(RAGGenerationPrompt):
    """
    Default prompt template used in the language generation step of RAG.
    """

    SCHEMA = DefaultRAGGenerationPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template used in the language generation step of RAG.",
        es="Plantilla de prompt predeterminada utilizada en el paso de"
        " generación de lenguaje de RAG.",
        pt="Modelo de prompt padrão usado na etapa de geração de linguagem do RAG.",
        de="Standard-Prompt-Vorlage, die im Sprachgenerierungsschritt von"
        " RAG verwendet wird.",
        zh="用于 RAG 语言生成步骤的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default RAG Generation Prompt",
        es="Prompt de Generación RAG Predeterminado",
        pt="Prompt de Geração RAG Padrão",
        de="Standard-RAG-Generierungs-Prompt",
        zh="默认 RAG 生成提示词",
    )

    metadata = {
        "name": "Default RAG Generation Prompt",
        "description": "Default prompt template used in the language"
        " generation step of RAG.",
        "type": "generation",
        "required_placeholders": RAGGenerationPrompt.required_placeholders,
        "optional_placeholders": RAGGenerationPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The user input message.",
            "{chunks}": "The document chunks to be included in the context.",
            "{queries}": (
                "The search queries used for retrieval (transformed queries "
                "when query transformation is enabled). The line containing "
                "this placeholder is removed when not supplied."
            ),
        },
        "templates": TEMPLATES,
    }

    required_placeholders = ["{input}", "{chunks}"]
    optional_placeholders = ["{queries}"]

    def __init__(self, **kwargs):
        """Initialize the default RAG generation prompt.

        Args:
            language: Language code (one of "en", "es", "pt").
            template: The prompt template string.
        """
        self.language = kwargs.pop("language")
        self.template = kwargs.pop("template")

    def format(
        self,
        input: str,
        chunks: str,
        queries: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Render the prompt by replacing placeholders with actual values.

        Args:
            input: The user's input message.
            chunks: Retrieved document chunks to include as context.
            queries: The search queries used for retrieval, or None when the
                query transformation stage is disabled. When None, the line
                containing ``{queries}`` is removed.
            **kwargs: Additional formatting parameters.

        Returns:
            The fully formatted prompt string.

        Raises:
            RAGPromptTemplateError: If the template is missing required
                placeholders.
        """
        if not self.validate_template(self.template):
            raise RAGPromptTemplateError(
                "Template is missing required placeholders:"
                f" {self.required_placeholders}"
            )
        # Optional placeholders resolve on the raw template first so input text
        # containing a token such as ``{queries}`` is never mistaken for the
        # template's own token. Required substitution is then single-pass, so
        # inserted text is not re-expanded.
        buffer = self.render_queries(self.template, queries)
        return self.render_placeholders(buffer, {"{input}": input, "{chunks}": chunks})
