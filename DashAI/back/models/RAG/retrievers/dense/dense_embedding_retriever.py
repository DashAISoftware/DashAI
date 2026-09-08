from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever

METRICS = ["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"]


class DenseEmbeddingRetrieverSchema(BaseSchema):
    """Schema for :class:`DenseEmbeddingRetriever`.

    Attributes:
        embedding_model: The embedding model component to use.
        similarity_metric: Distance metric for vector comparison.
        top_k: Number of chunks to select.
    """

    embedding_model: schema_field(
        component_field(parent="DenseEmbedding"),
        placeholder={"component": "SentenceTransformerEmbedding", "params": {}},
        description=MultilingualString(
            en="Embedding model to use for encoding chunks.",
            es="Modelo de embedding a usar para codificar fragmentos.",
            pt="Modelo de embedding a usar para codificar fragmentos.",
            de="Embedding-Modell zum Kodieren von Chunks.",
            zh="用于对块进行编码的嵌入模型。",
        ),
    )  # type: ignore

    similarity_metric: schema_field(
        enum_field(enum=METRICS),
        placeholder="cosine",
        description=MultilingualString(
            en="Distance metric for comparing dense vectors.",
            es="Métrica de distancia para comparar vectores densos.",
            pt="Métrica de distância para comparar vetores densos.",
            de="Distanzmetrik zum Vergleichen dichter Vektoren.",
            zh="用于比较稠密向量的距离度量。",
        ),
    )  # type: ignore

    top_k: schema_field(
        int_field(gt=0),
        placeholder=5,
        description=MultilingualString(
            en="Number of chunks to select.",
            es="Número de fragmentos a seleccionar.",
            pt="Número de fragmentos a selecionar.",
            de="Anzahl der auszuwählenden Chunks.",
            zh="要选择的块数量。",
        ),
    )  # type: ignore


class DenseEmbeddingRetriever(DenseRetriever):
    """Concrete dense retriever that accepts any :class:`DenseEmbedding` component.

    The embedding component is specified in the schema and instantiated
    by the factory via ``fill_objects``.
    """

    SCHEMA = DenseEmbeddingRetrieverSchema

    DISPLAY_NAME: str = MultilingualString(
        en="Dense Embedding Retriever",
        es="Recuperador por Embeddings Densos",
        pt="Recuperador por Embeddings Densos",
        de="Dense-Embedding-Retriever",
        zh="稠密嵌入检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense retriever using any registered DenseEmbedding for similarity search.",
        es="Recuperador denso que usa cualquier DenseEmbedding registrado"
        " para búsqueda por similitud.",
        pt="Recuperador denso que usa qualquer DenseEmbedding registrado"
        " para busca por similaridade.",
        de="Dichter Retriever, der jedes registrierte DenseEmbedding für"
        " die Ähnlichkeitssuche verwendet.",
        zh="使用任何已注册的 DenseEmbedding 进行相似性搜索的稠密检索器。",
    )

    def __init__(self, **kwargs):
        """Initialize the dense embedding retriever.

        Pops the ``embedding_model`` instance from kwargs and stores it.

        Args:
            **kwargs: Must contain ``embedding_model``,
                ``similarity_metric``, and ``top_k``.
        """
        embedding_instance = kwargs.pop("embedding_model")
        super().__init__(**kwargs)
        self.params["embedding_model"] = {
            "component": embedding_instance.__class__.__name__,
            "params": dict(sorted(embedding_instance.params.items())),
        }
        self._embedding_instance = embedding_instance

    def init_model(self) -> None:
        """Load the embedding model, then initialise the similarity matrix.

        The embedding instance is created by :meth:`fill_objects` during
        factory construction but its heavy resources (tokenizer, weights)
        are only acquired on the explicit ``load()`` call.
        """
        self._embedding_instance.load()
        self._init_embedding(self._embedding_instance)
