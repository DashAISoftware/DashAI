"""Abstract contract for query transformation prompts.

A transformation prompt renders a user message plus a conversation-history
block into a single chat instruction. It never declares a ``TYPE`` of its
own: every concrete prompt registers under the generic ``"Prompt"`` type via
:class:`~DashAI.back.models.RAG.prompts.base_prompt.BasePrompt`.
"""

from __future__ import annotations

from typing import Any

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt


class QueryTransformationPrompt(BasePrompt):
    """Base contract for prompts used by the query transformation stage.

    Templates are rendered with plain literal ``.replace`` calls rather than
    ``str.format`` because the function-call JSON contract embedded in the
    templates contains braces that ``str.format`` would try to interpret.

    Optional placeholders vanish together with the whole physical line that
    contains their token when no value is supplied. That lets a template say
    "Do not produce more than {n_max} sub-queries." and have the sentence
    disappear entirely when the cap is not configured, instead of leaving a
    dangling fragment of text.
    """

    required_placeholders = ["{input}", "{history}"]
    optional_placeholders: list[str] = []

    metadata = {
        "type": "transformation",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message that must be transformed.",
            "{history}": (
                "The conversation context block built from the previous "
                "messages; an empty string when there are no previous messages."
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
        required substitution stops inserted values being re-expanded.

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

    def format(self, input: str, history: str, **kwargs: Any) -> str:
        """Render the prompt for the transformation stage.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        **kwargs
            Technique-specific values (for example ``n`` or ``n_max``).

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


class QueryRewritingPrompt(QueryTransformationPrompt):
    """Anchor for 1-to-1 query rewriting prompts.

    A rewriting prompt takes ``(input, history)`` and produces a single
    self-contained search query.
    """

    required_placeholders = ["{input}", "{history}"]
    optional_placeholders = []

    def format(self, input: str, history: str, **kwargs: Any) -> str:
        """Render a rewriting prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        **kwargs
            Unused.

        Raises
        ------
        NotImplementedError
            Always; concrete subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class QueryExpansionPrompt(QueryTransformationPrompt):
    """Anchor for 1-to-``n`` query expansion prompts.

    An expansion prompt takes ``(input, history, n)`` and produces ``n``
    search queries or keyword phrases.
    """

    required_placeholders = ["{input}", "{history}", "{n}"]
    optional_placeholders = []

    def format(self, input: str, history: str, n: int, **kwargs: Any) -> str:
        """Render an expansion prompt.

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

        Raises
        ------
        NotImplementedError
            Always; concrete subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class QueryDecompositionPrompt(QueryTransformationPrompt):
    """Anchor for 1-to-``n`` query decomposition prompts.

    A decomposition prompt takes ``(input, history, n_max)`` and produces a
    variable number of independently retrievable sub-queries chosen by the
    model. ``n_max`` is an optional upper bound.
    """

    required_placeholders = ["{input}", "{history}"]
    optional_placeholders = ["{n_max}"]

    def format(
        self,
        input: str,
        history: str,
        n_max: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render a decomposition prompt.

        Parameters
        ----------
        input : str
            The current user message.
        history : str
            The already-formatted conversation history block.
        n_max : int | None
            Optional upper bound on the number of sub-queries. When ``None``
            the cap line is removed from the template.
        **kwargs
            Unused.

        Raises
        ------
        NotImplementedError
            Always; concrete subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")
