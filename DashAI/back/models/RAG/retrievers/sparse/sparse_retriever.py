from DashAI.back.core.utils import MultilingualString
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
