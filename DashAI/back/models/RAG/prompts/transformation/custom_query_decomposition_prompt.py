"""User-defined 1-to-n query decomposition prompt."""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.prompts.transformation.transformation_prompt import (
    QueryDecompositionPrompt,
)


class CustomQueryDecompositionPrompt(QueryDecompositionPrompt):
    """User-defined prompt template for 1-to-n query decomposition."""

    metadata = {
        "name": "Custom Query Decomposition Prompt",
        "description": "User-defined prompt template for 1-to-n query decomposition.",
        "type": "transformation",
        "technique": "decomposition",
        "variant": "custom",
        "required_placeholders": QueryDecompositionPrompt.required_placeholders,
        "optional_placeholders": QueryDecompositionPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message to decompose.",
            "{history}": (
                "The conversation context block; empty when there are no "
                "previous messages."
            ),
            "{n_max}": (
                "Optional upper bound on the number of sub-queries; the whole "
                "cap sentence disappears when it is not provided."
            ),
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the custom decomposition prompt.

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

    def format(
        self,
        input: str,
        history: str,
        n_max: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the custom decomposition prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        n_max : int | None
            Optional upper bound on the number of sub-queries. When ``None``
            the cap line is removed from the rendered prompt.
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
            {"{n_max}": n_max},
        )
