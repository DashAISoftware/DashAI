"""Abstract contract for retrieval sufficiency evaluation prompts.

An evaluation prompt renders the current user message plus the chunks already
retrieved into a single chat instruction that asks the model to decide whether
those chunks are enough to answer the message, and — when they are not — which
retrievers to consult next. It never declares a ``TYPE`` of its own: every
concrete prompt registers under the generic ``"Prompt"`` type via
:class:`~DashAI.back.models.RAG.prompts.base_prompt.BasePrompt`.
"""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt


class RetrievalSufficiencyPrompt(BasePrompt):
    """Base contract for prompts used by the LLM-evaluated retrievers.

    Templates are rendered with plain literal ``.replace`` calls rather than
    ``str.format`` because the strict JSON output contract embedded in the
    templates contains braces that ``str.format`` would try to interpret.

    Optional placeholders vanish together with the whole physical line that
    contains their token when no value is supplied, so a child-retriever
    catalog or a pool-size sentence disappears entirely instead of leaving a
    dangling fragment of text.
    """

    required_placeholders = ["{input}", "{chunks}"]
    optional_placeholders = ["{children_catalog}", "{pool_size}"]

    metadata = {
        "type": "evaluation",
        "technique": "sufficiency",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message the retrieved chunks must answer.",
            "{chunks}": (
                "The block of already-retrieved chunks under evaluation; empty "
                "when the previous retrieval round returned nothing."
            ),
            "{children_catalog}": (
                "Optional block listing the child retrievers as "
                '"index: retriever name"; the whole line disappears when it is '
                "not provided."
            ),
            "{pool_size}": (
                "Optional total number of candidate chunks in the current pool; "
                "the whole line disappears when it is not provided."
            ),
        },
    }

    @classmethod
    def _render(
        cls,
        template: str,
        required: dict[str, Any],
        optional: dict[str, Any] | None = None,
    ) -> str:
        """Render a template in the mandated order.

        Optional placeholders are resolved first, directly on the raw template
        (dropping whole lines when their value is ``None``); required
        placeholders are substituted afterwards in a single pass. Resolving the
        optionals first is what lets a user message or chunk that literally
        contains an optional token survive verbatim, and the single-pass
        required substitution stops inserted values from being re-expanded.

        Parameters
        ----------
        template : str
            The raw template.
        required : dict[str, Any]
            Mapping of required placeholder token to replacement value.
        optional : dict[str, Any] | None
            Mapping of optional placeholder token to replacement value.
            ``None`` maps (or a ``None`` value) drop the token's lines.

        Returns
        -------
        str
            The rendered template.
        """
        buffer = template
        if optional:
            for key, value in optional.items():
                buffer = BasePrompt.render_optional(buffer, key, value)
        return BasePrompt.render_placeholders(buffer, required)

    def _validate(self) -> None:
        """Ensure the resolved template carries every required placeholder.

        Raises
        ------
        RAGPromptTemplateError
            If a required placeholder is missing.
        """
        if not self.validate_template(self.template):
            raise RAGPromptTemplateError(
                "Template is missing required placeholders:"
                f" {self.required_placeholders}"
            )

    def format(
        self,
        input: str,
        chunks: str,
        children_catalog: str | None = None,
        pool_size: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the prompt for the retrieval sufficiency stage.

        Parameters
        ----------
        input : str
            The current user message.
        chunks : str
            The already-formatted block of retrieved chunks.
        children_catalog : str | None
            Optional child-retriever catalog; the owning line is dropped when
            ``None``.
        pool_size : int | None
            Optional candidate pool size; the owning line is dropped when
            ``None``.
        **kwargs
            Unused.

        Returns
        -------
        str
            The fully rendered prompt.

        Raises
        ------
        NotImplementedError
            Always; concrete subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")
