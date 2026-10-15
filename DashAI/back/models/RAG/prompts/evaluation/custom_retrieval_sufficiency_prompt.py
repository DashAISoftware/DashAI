"""User-defined retrieval sufficiency evaluation prompt."""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.prompts.evaluation.retrieval_sufficiency_prompt import (
    RetrievalSufficiencyPrompt,
)


class CustomRetrievalSufficiencyPrompt(RetrievalSufficiencyPrompt):
    """User-defined prompt template for judging retrieval sufficiency."""

    metadata = {
        "name": "Custom Retrieval Sufficiency Prompt",
        "description": "User-defined prompt template for judging retrieval"
        " sufficiency and choosing which retrievers to consult next.",
        "type": "evaluation",
        "technique": "sufficiency",
        "required_placeholders": RetrievalSufficiencyPrompt.required_placeholders,
        "optional_placeholders": RetrievalSufficiencyPrompt.optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message the chunks must answer.",
            "{chunks}": (
                "The already-retrieved chunks under evaluation; empty when the "
                "previous round returned nothing."
            ),
            "{children_catalog}": (
                "Optional child-retriever catalog; the whole line disappears "
                "when it is not provided."
            ),
            "{pool_size}": (
                "Optional candidate pool size; the whole line disappears when "
                "it is not provided."
            ),
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the custom sufficiency prompt.

        Parameters
        ----------
        template : str
            The user-defined template. Must contain ``{input}`` and
            ``{chunks}``.

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
        chunks: str,
        children_catalog: str | None = None,
        pool_size: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the custom sufficiency prompt.

        Parameters
        ----------
        input : str
            The current user message.
        chunks : str
            The already-formatted block of retrieved chunks.
        children_catalog : str | None
            Optional child-retriever catalog. When ``None`` the owning line is
            removed from the rendered prompt.
        pool_size : int | None
            Optional candidate pool size. When ``None`` the owning line is
            removed from the rendered prompt.
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
            {"{input}": input, "{chunks}": chunks},
            {"{children_catalog}": children_catalog, "{pool_size}": pool_size},
        )
