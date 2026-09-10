from typing import Any

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
        "You are a question-answering assistant with access to a set of "
        "retrieved documents.\n"
        "Your task is to answer the user's question using ONLY the "
        "information found in the documents below. If the documents do "
        "not contain enough information to answer the question, respond "
        'with "I don\'t know" and explain what information is missing.\n'
        "Cite relevant passages from the documents to support your answer.\n"
        "\n"
        "User question:\n"
        "{input}\n"
        "\n"
        "Retrieved documents:\n"
        "{chunks}\n"
        "\n"
        "Answer:"
    ),
    "es": (
        "Eres un asistente de preguntas y respuestas con acceso a un "
        "conjunto de documentos recuperados.\n"
        "Tu tarea es responder la pregunta del usuario usando SOLAMENTE "
        "la información encontrada en los documentos a continuación. Si "
        "los documentos no contienen suficiente información para responder "
        'la pregunta, responde con "No lo sé" y explica qué información '
        "falta.\n"
        "Cita pasajes relevantes de los documentos para respaldar tu "
        "respuesta.\n"
        "\n"
        "Pregunta del usuario:\n"
        "{input}\n"
        "\n"
        "Documentos recuperados:\n"
        "{chunks}\n"
        "\n"
        "Respuesta:"
    ),
    "pt": (
        "Você é um assistente de perguntas e respostas com acesso a um "
        "conjunto de documentos recuperados.\n"
        "Sua tarefa é responder à pergunta do usuário usando SOMENTE as "
        "informações encontradas nos documentos abaixo. Se os documentos "
        "não contiverem informações suficientes para responder à pergunta, "
        'responda com "Não sei" e explique quais informações estão '
        "faltando.\n"
        "Cite passagens relevantes dos documentos para apoiar sua "
        "resposta.\n"
        "\n"
        "Pergunta do usuário:\n"
        "{input}\n"
        "\n"
        "Documentos recuperados:\n"
        "{chunks}\n"
        "\n"
        "Resposta:"
    ),
}


class DefaultQARAGGenerationPromptSchema(BaseSchema):
    """Schema for the default QA RAG generation prompt.

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


class DefaultQARAGGenerationPrompt(RAGGenerationPrompt):
    """
    Default generation prompt for Question Answering tasks.
    This prompt is designed to guide the language model in generating
    answers based on provided context chunks.
    """

    SCHEMA = DefaultQARAGGenerationPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template used in the language generation step"
        " of RAG for Question Answering tasks.",
        es="Plantilla de prompt predeterminada utilizada en el paso de"
        " generación de lenguaje de RAG para tareas de preguntas y"
        " respuestas.",
        pt="Modelo de prompt padrão usado na etapa de geração de linguagem"
        " do RAG para tarefas de perguntas e respostas.",
        de="Standard-Prompt-Vorlage, die im Sprachgenerierungsschritt von"
        " RAG für Frage-Antwort-Aufgaben verwendet wird.",
        zh="用于问答任务的 RAG 语言生成步骤中的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default QA RAG Generation Prompt",
        es="Prompt de Generación RAG de Preguntas y Respuestas Predeterminado",
        pt="Prompt de Geração RAG de Perguntas e Respostas Padrão",
        de="Standard-QA-RAG-Generierungs-Prompt",
        zh="默认 QA RAG 生成提示词",
    )

    metadata = {
        "name": "Default QA RAG Generation Prompt",
        "description": "Default prompt template used in the language"
        " generation step of RAG for Question Answering tasks.",
        "type": "generation",
        "required_placeholders": RAGGenerationPrompt.required_placeholders,
        "optional_placeholders": RAGGenerationPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The user input message.",
            "{chunks}": "The document chunks to be included in the context.",
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs):
        """Initialize the default QA RAG generation prompt.

        Args:
            language: Language code (one of "en", "es", "pt").
            template: The prompt template string.
        """
        self.language = kwargs.pop("language")
        self.template = kwargs.pop("template")

    def format(self, input: str, chunks: str, **kwargs: Any) -> str:
        """Render the QA prompt by replacing placeholders with actual values.

        Args:
            input: The user's question.
            chunks: Retrieved document chunks to include as context.
            **kwargs: Additional formatting parameters.

        Returns:
            The fully formatted QA prompt string.

        Raises:
            RAGPromptTemplateError: If the template is missing required
                placeholders.
        """
        if not self.validate_template(self.template):
            raise RAGPromptTemplateError(
                "Template is missing required placeholders:"
                f" {self.required_placeholders}"
            )
        buffer = self.template
        buffer = buffer.replace("{input}", input)
        buffer = buffer.replace("{chunks}", chunks)
        return buffer
