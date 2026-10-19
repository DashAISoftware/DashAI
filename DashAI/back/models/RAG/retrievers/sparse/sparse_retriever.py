from typing import Dict

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.unit_retriever import UnitRetriever


class SparseRetriever(UnitRetriever):
    """Abstract base for sparse (keyword-based) retrievers.

    Uses term-frequency based representations (e.g. TF-IDF, BM25) for
    document retrieval.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Keyword Retriever",
        es="Recuperador por Palabras Clave",
        pt="Recuperador por Palavras-chave",
        de="Stichwort-Retriever",
        zh="关键词检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Sparse retriever using term-frequency based representations.",
        es="Recuperador disperso que usa representaciones basadas en"
        " frecuencia de términos.",
        pt="Recuperador disperso que usa representações baseadas em"
        " frequência de termos.",
        de="Sparser Retriever, der auf Termhäufigkeit basierende"
        " Darstellungen verwendet.",
        zh="使用基于词频表示的稀疏检索器。",
    )
    CATEGORY: MultilingualString = MultilingualString(
        en="Keyword retrievers",
        es="Recuperadores por palabras clave",
        pt="Recuperadores por palavras-chave",
        de="Stichwort-Retriever",
        zh="关键词检索器",
    )

    def _chunks_by_id(self) -> Dict[int, Chunk]:
        """Return the chunks the retriever was given, keyed by chunk id.

        The saved row maps hold only chunk ids, so the chunk text is read
        from the chunk set rather than kept in the retriever files.

        Returns
        -------
        Dict[int, Chunk]
            Every chunk of every document, keyed by ``Chunk.id``.
        """
        return {
            chunk.id: chunk
            for document_chunks in self.chunks.values()
            for chunk in document_chunks.values()
        }
