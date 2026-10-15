from typing import Any, Optional

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.generation.RAG_generation_prompt import (
    RAGGenerationPrompt,
)


class CustomRAGGenerationPrompt(RAGGenerationPrompt):
    """
    CustomRAGGenerationPrompt class for user-defined prompt templates
    used in the language generation step of RAG.
    """

    metadata = {
        "name": "Custom RAG Generation Prompt",
        "description": "User-defined prompt template used in the language"
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
    }

    def __init__(self, **kwargs: Any):
        """Initialize the custom RAG generation prompt.

        Args:
            template: The user-defined prompt template string.
        """
        self.template = kwargs.pop("template")

    def format(
        self,
        input: str,
        chunks: str,
        queries: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Format the prompt using the provided template.

        Args:
            input (str): The user input message.
            chunks (List[str]): The document chunks to be included in the
                context.
            queries (Optional[str]): The search queries used for retrieval, or
                None when query transformation is disabled. When None, any line
                containing ``{queries}`` is removed from the template.
            **kwargs: Additional keyword arguments for formatting.

        Returns:
            str: The formatted prompt.
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
