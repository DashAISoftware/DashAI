"""Abstract contract for retrieval sufficiency evaluation prompts.

An evaluation prompt renders the current user message plus the chunks already
retrieved into a single chat instruction that asks the model to decide whether
those chunks are enough to answer the message, and — when they are not — which
retrievers to consult next. It never declares a ``TYPE`` of its own: every
concrete prompt registers under the generic ``"Prompt"`` type via
:class:`~DashAI.back.models.RAG.prompts.base_prompt.BasePrompt`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, List

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt
from DashAI.back.models.RAG.retrievers.retrieval_contracts import (
    CHUNK_DOCUMENT_ID,
    CHUNK_POSITION,
    CHUNK_TEXT,
    DOCUMENT_ID,
    DOCUMENT_NAME,
    ChunkPayload,
    DocumentSummary,
    RetrieverCatalog,
)

#: Maximum number of characters of each chunk's text rendered into a prompt.
_CHUNK_TEXT_LIMIT = 400


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
    optional_placeholders = [
        "{children_catalog}",
        "{pool_size}",
        "{topk}",
        "{retriever.description}",
        "{documents.names}",
        "{documents.description}",
    ]

    metadata = {
        "type": "evaluation",
        "technique": "sufficiency",
        "required_placeholders": required_placeholders,
        "optional_placeholders": optional_placeholders,
        "placeholder_descriptions": {
            "{input}": "The current user message the retrieved chunks must answer.",
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
                "Optional total number of candidate chunks in the current pool; "
                "the whole line disappears when it is not provided."
            ),
            "{topk}": (
                "Optional maximum number of chunks the retriever may return; "
                "the whole line disappears when it is not provided."
            ),
            "{retriever.description}": (
                "Optional JSON catalog of the child retrievers and their "
                "parameters; the whole line disappears when it is not provided."
            ),
            "{documents.names}": (
                "Optional comma-separated names of the documents in the corpus; "
                "the whole line disappears when it is not provided."
            ),
            "{documents.description}": (
                "Optional JSON summary of the documents (id, name, chunk count "
                "and pages); the whole line disappears when it is not provided."
            ),
        },
    }

    @staticmethod
    def _render_optional_value(value: Any) -> Any:
        """Render mapping/sequence placeholder values as indented JSON.

        Notes
        -----
        Strings and scalars are returned unchanged so ``_render`` still
        stringifies them and ``None`` keeps dropping the owning line.
        """
        if isinstance(value, Mapping):
            return json.dumps(dict(value), ensure_ascii=False, indent=2)
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value), ensure_ascii=False, indent=2)
        return value

    @staticmethod
    def _format_chunks(chunks: str | Sequence[ChunkPayload]) -> str:
        """Render chunk provenance lines, or keep a preformatted string.

        Parameters
        ----------
        chunks : str | Sequence[Mapping[str, Any]]
            Either an already-rendered block (returned verbatim) or structured
            payloads carrying ``document_id``, ``position`` and ``text``.

        Returns
        -------
        str
            One ``[i] (document_id=..., position=...) <text>`` line per chunk.
        """
        if isinstance(chunks, str):
            return chunks
        lines: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            if not isinstance(chunk, Mapping):
                raise RAGPromptTemplateError(
                    f"Chunk payload {index} must be a mapping, got "
                    f"{type(chunk).__name__}."
                )
            missing: List[str] = []
            for key in (CHUNK_DOCUMENT_ID, CHUNK_POSITION, CHUNK_TEXT):
                if key not in chunk:
                    missing.append(key)
            if missing:
                raise RAGPromptTemplateError(
                    f"Chunk payload {index} is missing required keys: "
                    f"{', '.join(missing)}."
                )
            raw_text = str(chunk[CHUNK_TEXT])
            text = raw_text[:_CHUNK_TEXT_LIMIT]
            if len(raw_text) > _CHUNK_TEXT_LIMIT:
                text += "..."
            lines.append(
                f"[{index}] ({CHUNK_DOCUMENT_ID}={chunk[CHUNK_DOCUMENT_ID]}, "
                f"{CHUNK_POSITION}={chunk[CHUNK_POSITION]}) {text}"
            )
        return "\n".join(lines)

    @classmethod
    def _format_documents(
        cls, documents: Sequence[DocumentSummary] | None
    ) -> tuple[str | None, str | None]:
        """Return the document names and JSON description for the prompt.

        Parameters
        ----------
        documents : Sequence[DocumentSummary] | None
            Structured document summaries supplied by the retrieval context.

        Returns
        -------
        tuple[str | None, str | None]
            The comma-separated display names and the JSON description, or
            ``(None, None)`` when no documents are supplied.
        """
        if not documents:
            return None, None
        names: List[str] = []
        for document in documents:
            name = document.get(DOCUMENT_NAME)
            if not name:
                name = f"document {document.get(DOCUMENT_ID)}"
            names.append(str(name))
        return ", ".join(names), cls._render_optional_value(documents)

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
        chunks: str | Sequence[ChunkPayload],
        children_catalog: str | RetrieverCatalog | None = None,
        pool_size: int | None = None,
        top_k: int | None = None,
        retrievers: str | RetrieverCatalog | None = None,
        documents: Sequence[DocumentSummary] | None = None,
    ) -> str:
        """Render the prompt for the retrieval sufficiency stage.

        The retriever passes structured data only; this method owns every piece
        of prompt formatting.

        Parameters
        ----------
        input : str
            The current user message.
        chunks : str | Sequence[Mapping[str, Any]]
            Preformatted chunk text (kept verbatim) or structured chunk payloads
            with ``document_id``, ``position`` and ``text``.
        children_catalog : str | Mapping | None
            Legacy alias for ``retrievers``; ``retrievers`` wins when both are
            supplied.
        pool_size : int | None
            Optional candidate pool size.
        top_k : int | None
            Optional maximum number of retrievable chunks.
        retrievers : str | Mapping | None
            Optional 1-based retriever catalog, JSON-rendered.
        documents : Sequence[DocumentSummary] | None
            Optional document summaries; names and JSON are derived from them.

        Returns
        -------
        str
            The fully rendered prompt.

        Raises
        ------
        RAGPromptTemplateError
            If the template is missing required placeholders or a structured
            chunk payload is malformed.
        """
        self._validate()
        catalog_value = retrievers if retrievers is not None else children_catalog
        documents_names, documents_description = self._format_documents(documents)
        return self._render(
            self.template,
            {
                "{input}": input,
                "{chunks}": self._format_chunks(chunks),
            },
            {
                "{children_catalog}": self._render_optional_value(catalog_value),
                "{pool_size}": pool_size,
                "{topk}": top_k,
                "{retriever.description}": self._render_optional_value(catalog_value),
                "{documents.names}": documents_names,
                "{documents.description}": documents_description,
            },
        )
