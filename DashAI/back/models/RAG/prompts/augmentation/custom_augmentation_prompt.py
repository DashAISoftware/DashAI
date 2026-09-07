from typing import Any

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.augmentation import AugmentationPrompt


class CustomAugmentationPrompt(AugmentationPrompt):
    """
    User-defined augmentation prompt template for generating augmented retrieval
    prompts.
    It uses the language model to generate keywords or phrases that can be used
    to augment the input.
    """

    metadata = {
        "name": "Custom Augmentation Prompt",
        "description": "User-defined prompt template for generating augmented "
        "retrieval prompts.",
        "type": "augmentation",
        "required_placeholders": AugmentationPrompt.required_placeholders,
        "optional_placeholders": AugmentationPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The user input message.",
            "{n_search_terms}": "The number of search terms to generate.",
        },
    }

    required_placeholders = ["{input}", "{n_search_terms}"]
    optional_placeholders = []

    def __init__(self, **kwargs):
        """Initialize the custom augmentation prompt with a user-defined template.

        Args:
            template: The user-defined prompt template string.
        """
        self.template = kwargs.pop("template")
        super().__init__(**kwargs)

    def format(
        self,
        input: str,
        n_search_terms: int,
        **kwargs: Any,
    ) -> str:
        """
        Instantiate and format the prompt for augmentation.
        Args:
            input (str): The input to be formatted.
            n_search_terms (int): The number of search terms to generate.
            **kwargs: Additional keyword arguments for formatting.
        Returns:
            str: The formatted prompt.
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
