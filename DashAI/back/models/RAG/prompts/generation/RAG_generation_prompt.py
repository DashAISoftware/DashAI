from typing import Any

from DashAI.back.models.RAG.prompts.prompt import Prompt


class RAGGenerationPrompt(Prompt):
    """
    RAGGenerationPrompt class for formatting prompts used in the language
    generation step of RAG.
    """

    required_placeholders = ["{input}", "{chunks}"]
    optional_placeholders = []

    def format(
        self,
        input: str,
        chunks: str,
        **kwargs: Any,
    ) -> str:
        """Format the generation prompt with user input and context chunks.

        Args:
            input: The user's input message.
            chunks: Retrieved document chunks to include as context.
            **kwargs: Additional formatting parameters.

        Returns:
            The formatted prompt string.
        """
        raise NotImplementedError("Subclasses must implement this method.")
