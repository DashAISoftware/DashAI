from typing import Any

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.augmentation.augmentation_prompt import (
    AugmentationPrompt,
)

TEMPLATES = {
    "en": (
        "You are an intelligent and insightful assistant. Your task is to generate "
        "keywords or phrases to search for relevant information based on the input "
        "provided.\n"
        "The keywords or phrases should be relevant to the input and should help in "
        "retrieving useful information to improve the precision of the response.\n"
        "\n"
        "User input:\n"
        "{input}\n"
        "\n"
        "Generate {n_search_terms} keywords or phrases that can be used to search for "
        "relevant information. The keywords or phrases should be concise and to the "
        "point.\n"
        "\n"
        "You must respond with a JSON object following this exact format:\n"
        "{'keywords': ['keyword_1', 'keyword_2', ..., 'keyword_n']}"
    ),
    "es": (
        "Eres un asistente inteligente y perspicaz. Tu tarea es generar palabras clave "
        "o frases para buscar información relevante basada en la entrada "
        "proporcionada.\n"
        "Las palabras clave o frases deben ser relevantes para la entrada y ayudar a "
        "recuperar información útil para mejorar la precisión de la respuesta.\n"
        "\n"
        "Entrada del usuario:\n"
        "{input}\n"
        "\n"
        "Genera {n_search_terms} palabras clave o frases que puedan usarse para buscar "
        "información relevante. Las palabras clave o frases deben ser concisas y "
        "directas.\n"
        "\n"
        "Debes responder con un objeto JSON siguiendo este formato exacto:\n"
        "{'keywords': ['palabra_clave_1', 'palabra_clave_2', ..., 'palabra_clave_n']}"
    ),
    "pt": (
        "Você é um assistente inteligente e perspicaz. Sua tarefa é gerar "
        "palavras-chave ou frases para buscar informações relevantes com base na "
        "entrada fornecida.\n"
        "As palavras-chave ou frases devem ser relevantes para a entrada e ajudar a "
        "recuperar informações úteis para melhorar a precisão da resposta.\n"
        "\n"
        "Entrada do usuário:\n"
        "{input}\n"
        "\n"
        "Gere {n_search_terms} palavras-chave ou frases que possam ser usadas para "
        "buscar informações relevantes. As palavras-chave ou frases devem ser concisas "
        "e diretas.\n"
        "\n"
        "Você deve responder com um objeto JSON seguindo este formato exato:\n"
        "{'keywords': ['palavra_chave_1', 'palavra_chave_2', ..., 'palavra_chave_n']}"
    ),
}


class DefaultAugmentationPromptSchema(BaseSchema):
    """Schema for the default augmentation prompt.

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


class DefaultAugmentationPrompt(AugmentationPrompt):
    """Default prompt template for generating augmented retrieval queries."""

    SCHEMA = DefaultAugmentationPromptSchema
    DESCRIPTION: str = MultilingualString(
        en="Default prompt template for generating augmented retrieval queries.",
        es="Plantilla de prompt predeterminada para generar consultas de "
        "recuperación aumentadas.",
        pt="Modelo de prompt padrão para gerar consultas de recuperação aumentadas.",
        de="Standard-Prompt-Vorlage zum Erzeugen erweiterter Abruf-Abfragen.",
        zh="用于生成增强检索查询的默认提示词模板。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Default Augmentation Prompt",
        es="Prompt de Aumento Predeterminado",
        pt="Prompt de Aumento Padrão",
        de="Standard-Augmentierungs-Prompt",
        zh="默认增强提示词",
    )

    required_placeholders = ["{input}", "{n_search_terms}"]
    optional_placeholders: list[str] = []

    metadata = {
        "name": "Default Augmentation Prompt",
        "description": "Default prompt template for generating augmented retrieval "
        "prompts.",
        "type": "augmentation",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The user input message.",
            "{n_search_terms}": "The number of search terms to generate.",
        },
        "templates": TEMPLATES,
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the augmentation prompt with a language and resolved template.

        Args:
            language: Language code to select the appropriate template
                (one of "en", "es", "pt").
            template: Override template string. If not provided, the
                default template for the selected language is used.
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
        super().__init__(**kwargs)

    def format(
        self,
        input: str,
        n_search_terms: int,
        **kwargs: Any,
    ) -> str:
        """Render the augmentation prompt by replacing all placeholders.

        Args:
            input: The user's input message.
            n_search_terms: Number of search terms the LLM should generate.

        Returns:
            Fully formatted prompt string ready for LLM input.
        """
        if not self.validate_template(self.template):
            raise RAGPromptTemplateError(
                "Template is missing required placeholders:"
                f" {self.required_placeholders}"
            )
        buffer = self.template
        buffer = buffer.replace("{input}", input)
        buffer = buffer.replace("{n_search_terms}", str(n_search_terms))
        return buffer
