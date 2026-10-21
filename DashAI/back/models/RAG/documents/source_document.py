"""A Data module document as a RAG pipeline reads it."""

from dataclasses import dataclass

from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument


@dataclass(frozen=True)
class SourceDocument:
    """A parsed Data module document handed to a chunker.

    Parameters
    ----------
    id : int
        ``data_document`` primary key.
    file_name : str
        Name of the document, shown next to the chunks it answers with.
    content : DashAIDocument
        The parsed content.
    """

    id: int
    file_name: str
    content: DashAIDocument
