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
                "The chunks under evaluation, one line per chunk carrying its "
                "document_id, position and text; a preformatted string is kept "
                "verbatim."
            ),
            "{children_catalog}": (
                "Optional alias for the retriever catalog; the whole line "
                "disappears when it is not provided."
            ),
            "{pool_size}": (
                "Optional candidate pool size; the whole line disappears when "
                "it is not provided."
            ),
            "{topk}": (
                "Optional maximum number of retrievable chunks; the whole line "
                "disappears when it is not provided."
            ),
            "{retriever.description}": (
                "Optional JSON catalog of the retrievers; the whole line "
                "disappears when it is not provided."
            ),
            "{documents.names}": (
                "Optional comma-separated document names; the whole line "
                "disappears when it is not provided."
            ),
            "{documents.description}": (
                "Optional JSON document summary; the whole line disappears "
                "when it is not provided."
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
