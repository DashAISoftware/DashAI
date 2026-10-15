"""Trace helpers shared by every retriever.

A retriever's ``retrieve()`` returns ``(chunks, trace)``: the retrieved chunks
and a JSON-serializable *trace node* describing which chunks this retriever
returned and, for composite retrievers, which child nodes produced them.

The chunk reference string built here is the **single source of truth** for the
join key between the trace and the pipeline's ``Dict`` output row: the pipeline
keys its chunk map by the exact same ``"<document_id>_<position>"`` string, so
the frontend can join a trace reference to a chunk's text/record without
duplicating the chunk payload. The join is a LEFT-OUTER lookup: trace nodes may
reference chunks that did not survive to the pipeline's final chunk map (for
example cascade stages of a sequential retriever or re-rank candidates), so a
missing reference resolves to nothing and is not an error.
"""

from typing import Any, Dict, List

from DashAI.back.models.RAG.documents import Chunk


def chunk_ref(chunk: Chunk) -> str:
    """Build the canonical reference string for a chunk.

    The format is ``f"<document_id>_<document_position>"`` — the SAME string the
    pipeline uses as the ``Dict`` output row key. Keeping the format here is what
    lets a trace node reference a chunk without repeating its text.

    Parameters
    ----------
    chunk : Chunk
        The chunk to reference.

    Returns
    -------
    str
        The ``"<document_id>_<position>"`` reference string.
    """
    return f"{chunk.document_id}_{chunk.document_position}"


def retriever_trace(model: Any, chunks: List[Chunk], **extras: Any) -> Dict[str, Any]:
    """Build a trace node describing one retriever's run.

    Parameters
    ----------
    model : Any
        The retriever instance that produced *chunks*; its class name becomes
        the node's ``name``.
    chunks : List[Chunk]
        The chunks the retriever returned, in retrieval order. Their references
        become the node's ``chunks`` list.
    **extras : Any
        Technique-specific keys merged into the node (e.g. ``children`` for
        composites, ``scores`` for the cross-encoder).

    Returns
    -------
    Dict[str, Any]
        A trace node ``{"name", "chunks", **extras}`` whose references join the
        pipeline's ``Dict`` output row.
    """
    if "name" in extras or "chunks" in extras:
        raise ValueError(
            "Trace node keys 'name' and 'chunks' are canonical and cannot be "
            "overridden by extras."
        )
    return {
        "name": type(model).__name__,
        "chunks": [chunk_ref(chunk) for chunk in chunks],
        **extras,
    }
