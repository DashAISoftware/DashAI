from abc import abstractmethod

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.embeddings.dense.huggingface_embedding import (
    HuggingFaceEmbedding,
)
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever

METRICS = ["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"]


class HuggingFaceDenseRetriever(DenseRetriever):
    """Abstract dense retriever that creates a HuggingFace embedding model.

    Subclasses must implement :meth:`_create_embedding` to return a
    :class:`HuggingFaceEmbedding` instance with the desired model
    configuration.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="HuggingFace Embedding Retriever",
        es="Recuperador por Embeddings HuggingFace",
        pt="Recuperador por Embeddings HuggingFace",
        de="HuggingFace-Embedding-Retriever",
        zh="HuggingFace 嵌入检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense retriever using HuggingFace embeddings for similarity search.",
        es="Recuperador denso que usa embeddings HuggingFace para"
        " búsqueda por similitud.",
        pt="Recuperador denso que usa embeddings HuggingFace para"
        " busca por similaridade.",
        de="Dichter Retriever, der HuggingFace-Embeddings für die"
        " Ähnlichkeitssuche verwendet.",
        zh="使用 HuggingFace 嵌入进行相似性搜索的稠密检索器。",
    )

    def __init__(self, **kwargs):
        """Initialize the HuggingFace dense retriever.

        Args:
            **kwargs: Forwarded to :class:`DenseRetriever`.
        """
        super().__init__(**kwargs)

    @abstractmethod
    def _create_embedding(self) -> HuggingFaceEmbedding:
        """Create and return a HuggingFace embedding model.

        Returns:
            A :class:`HuggingFaceEmbedding` instance.
        """
        raise NotImplementedError

    def init_model(self) -> None:
        """Create, load, and initialise the HuggingFace embedding.

        Calls ``_create_embedding()``, loads its resources, then
        passes it to ``_init_embedding()``.
        """
        embedding = self._create_embedding()
        embedding.load()
        self._init_embedding(embedding)
