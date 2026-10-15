"""User-defined 1-to-1 query rewriting prompt."""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryRewritingPrompt,
)


class CustomQueryRewritingPrompt(QueryRewritingPrompt):
    """User-defined prompt template for 1-to-1 query rewriting."""

    metadata = {
        "name": "Custom Query Rewriting Prompt",
        "description": "User-defined prompt template for 1-to-1 query rewriting.",
        "type": "transformation",
        "technique": "rewriting",
        "required_placeholders": QueryRewritingPrompt.required_placeholders,
        "optional_placeholders": QueryRewritingPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to rewrite.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the custom rewriting prompt.

        Parameters
        ----------
        template : str
            The user-defined template. Must contain ``{input}`` and
            ``{history}``.

        Raises
        ------
        RAGPromptTemplateError
            If the template is missing a required placeholder.
        """
        self.template = kwargs.pop("template")
        self._validate()

    def format(self, input: str, history: str, **kwargs: Any) -> str:
        """Render the custom rewriting prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
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
            {"{input}": input, "{history}": history},
        )
