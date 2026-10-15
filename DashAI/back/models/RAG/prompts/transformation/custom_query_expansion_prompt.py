"""User-defined 1-to-n query expansion prompt."""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryExpansionPrompt,
)


class CustomQueryExpansionPrompt(QueryExpansionPrompt):
    """User-defined prompt template for 1-to-n query expansion."""

    metadata = {
        "name": "Custom Query Expansion Prompt",
        "description": "User-defined prompt template for 1-to-n query expansion.",
        "type": "transformation",
        "technique": "expansion",
        "variant": "custom",
        "required_placeholders": QueryExpansionPrompt.required_placeholders,
        "optional_placeholders": QueryExpansionPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to expand.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
            "{n}": "The exact number of queries the model must produce.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the custom expansion prompt.

        Parameters
        ----------
        template : str
            The user-defined template. Must contain ``{input}``,
            ``{history}`` and ``{n}``.

        Raises
        ------
        RAGPromptTemplateError
            If the template is missing a required placeholder.
        """
        self.template = kwargs.pop("template")
        self._validate()

    def format(self, input: str, history: str, n: int, **kwargs: Any) -> str:
        """Render the custom expansion prompt.

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
