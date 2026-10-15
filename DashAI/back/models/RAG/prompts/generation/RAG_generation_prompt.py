from typing import Any, Optional

from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt


class RAGGenerationPrompt(BasePrompt):
    """
    RAGGenerationPrompt class for formatting prompts used in the language
    generation step of RAG.

    Optional placeholder
    --------------------
    ``{queries}`` — the search queries used for retrieval. The pipeline
    supplies them when the optional query-transformation stage produced one or
    more queries (joined with ``"; "``). When the stage is disabled the value
    is ``None`` and the whole physical line containing the token is removed, so
    no dangling "search queries" section is left behind.
    """

    required_placeholders = ["{input}", "{chunks}"]
    optional_placeholders = ["{queries}"]

    @staticmethod
    def render_queries(template: str, queries: Optional[str]) -> str:
        """Render the optional ``{queries}`` placeholder.

        Reuses the shared line-drop contract from
        :meth:`DashAI.back.models.RAG.prompts.base_prompt.BasePrompt.render_optional`:
        when ``queries`` is ``None`` every physical line containing the token is
        removed; otherwise the token is replaced in place with
        ``str(queries)``.

        Parameters
        ----------
        template : str
            The template that may contain ``{queries}``.
        queries : str | None
            The already-joined search queries, or ``None`` when the query
            transformation stage is disabled.

        Returns
        -------
        str
            The rendered template.
        """
        return BasePrompt.render_optional(template, "{queries}", queries)

    def format(
        self,
        input: str,
        chunks: str,
        queries: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Format the generation prompt with user input and context chunks.

        Args:
            input: The user's input message.
            chunks: Retrieved document chunks to include as context.
            queries: The search queries used for retrieval, or None when the
                query transformation stage is disabled.
            **kwargs: Additional formatting parameters.

        Returns:
            The formatted prompt string.
        """
        raise NotImplementedError("Subclasses must implement this method.")
