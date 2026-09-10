from typing import Any

from DashAI.back.models.RAG.prompts.prompt import Prompt


class AugmentationPrompt(Prompt):
    """
    AugmentationPrompt class for generating augmented retrieval prompts,
    it uses the language model to generate keywords or phrases that can be used
    to augment the input.
    """

    required_placeholders = ["{input}", "{n_search_terms}"]
    optional_placeholders = []

    def __init__(self, **kwargs: Any):
        """Initialize the augmentation prompt with a template.

        Args:
            template: The prompt template string.
        """
        self.template = kwargs.pop("template")
        super().__init__(**kwargs)

    def format(self, input: str, n_search_terms: int, **kwargs: Any) -> str:
        """
        Instantiate and format the prompt for augmentation.
        Args:
            input (str): The input to be formatted.
            n_search_terms (int): The number of search terms to generate.
            **kwargs: Additional keyword arguments for formatting.
        Returns:
            str: The formatted prompt.
        """
        raise NotImplementedError("Subclasses must implement this method.")
