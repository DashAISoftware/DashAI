import os
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import pairwise_distances

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.embeddings import DenseEmbedding
from DashAI.back.models.RAG.exceptions import RAGRetrieverError
from DashAI.back.models.RAG.retrievers.unit_retriever import UnitRetriever

# NOTE: The entire chunk index (similarity_matrix) is loaded into memory,
# which is fine for typical use with tens to low hundreds of documents but
# may be a bottleneck for very large collections.


class DenseRetrieverSchema(BaseSchema):
    """Schema for :class:`DenseRetriever`.

    Attributes:
        similarity_metric: Distance metric for vector comparison.
        top_k: Number of chunks to select.
    """

    similarity_metric: schema_field(
        enum_field(enum=["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"]),
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


class DenseRetriever(UnitRetriever):
    """Abstract base for dense (embedding-based) retrievers.

    Maintains a similarity matrix of chunk embeddings loaded from
    on-disk ``.npy`` files and retrieves via pairwise distance.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Embedding Retriever",
        es="Recuperador por Embeddings",
        pt="Recuperador por Embeddings",
        de="Embedding-Retriever",
        zh="嵌入检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Embedding retriever using vector embeddings for similarity search.",
        es="Recuperador por embeddings que usa representaciones"
        " vectoriales para búsqueda por similitud.",
        pt="Recuperador por embeddings que usa representações vetoriais"
        " para busca por similaridade.",
        de="Embedding-Retriever, der Vektor-Embeddings für die"
        " Ähnlichkeitssuche verwendet.",
        zh="使用向量嵌入进行相似性搜索的嵌入检索器。",
    )

    SCHEMA = DenseRetrieverSchema

    def __init__(self, **kwargs):
        """Initialize the dense retriever.

        Args:
            **kwargs: Must contain ``similarity_metric`` and ``top_k``.
        """
        super().__init__(**kwargs)

        self.similarity_metric = self.params.pop("similarity_metric")
        self._top_k = self.params.pop("top_k")

    def _init_embedding(self, embedding_model):
        """Initialise the embedding model and build the similarity matrix.

        Args:
            embedding_model: A :class:`DenseEmbedding` instance used to
                encode chunks.

        Raises:
            TypeError: If *embedding_model* is not a ``DenseEmbedding``.
        """
        if not isinstance(embedding_model, DenseEmbedding):
            raise TypeError(
                f"Expected DenseEmbedding instance, "
                f"got {type(embedding_model).__name__}"
            )
        self.embedding_model = embedding_model
        self.compute_missing_embeddings()
        self.init_similarity_matrix()

    def compute_missing_embeddings(self):
        """Compute and persist embeddings for chunks that lack them.

        Iterates over all documents; if an ``embeddings.npy`` file does
        not yet exist at the expected path, the embedding model is used
        to encode the chunk texts and the result is saved.
        """
        for doc_id, doc_chunks in self.chunks.items():
            matrix_dir = self._persistence.matrix_dirs.get(doc_id)
            if matrix_dir is None:
                continue
            matrix_path = os.path.join(matrix_dir, "embeddings.npy")
            if os.path.exists(matrix_path):
                continue
            chunk_texts = [chunk.text for chunk in doc_chunks.values()]
            if not chunk_texts:
                raise RAGRetrieverError(f"No chunks found for document ID {doc_id}.")
            embeddings = self.embedding_model.batch_encode(chunk_texts)
            os.makedirs(matrix_dir, exist_ok=True)
            np.save(matrix_path, embeddings)

    def init_similarity_matrix(self):
        """Load all persisted embedding matrices into a single similarity matrix.

        Builds ``similarity_matrix`` (a vertical stack of all per-document
        embedding arrays), ``matrix_row_to_chunk_id`` (row -> chunk DB id),
        ``chunk_id_to_doc_id`` (chunk DB id -> document id), and
        ``_chunk_key_by_id`` (chunk DB id -> ``(document id, dict key)``)
        lookup mappings.

        Chunks are keyed by their persistent DB id (``Chunk.id``), which is
        what composite retrievers (MMR reranker, sequential, parallel,
        cross-encoder) pass to ``score_chunks`` / ``get_chunk_vectors``.
        """
        self.similarity_matrix = None
        self.matrix_row_to_chunk_id = {}
        self.chunk_id_to_doc_id = {}
        self._chunk_key_by_id: Dict[int, Tuple[int, int]] = {}

        all_embeddings = []
        row_index = 0
        for doc_id, chunks in self.chunks.items():
            matrix_dir = self._persistence.matrix_dirs.get(doc_id)
            if matrix_dir is None:
                continue
            matrix_path = os.path.join(matrix_dir, "embeddings.npy")
            if not os.path.exists(matrix_path):
                continue
            for chunk_key, chunk in chunks.items():
                chunk_id = chunk.id
                self.matrix_row_to_chunk_id[row_index] = chunk_id
                self.chunk_id_to_doc_id[chunk_id] = doc_id
                self._chunk_key_by_id[chunk_id] = (doc_id, chunk_key)
                row_index += 1
            all_embeddings.append(np.load(matrix_path))

        if all_embeddings:
            self.similarity_matrix = np.vstack(all_embeddings)

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k value.

        Returns:
            Number of chunks to retrieve.
        """
        return self._top_k

    def retrieve(self, query: str, top_k: int | None = None) -> List[Chunk]:
        """Retrieve the top-k chunks by embedding similarity.

        Args:
            query: The search query string.
            top_k: Override for the default ``top_k``. Uses the
                configured value if ``None``.

        Returns:
            A list of :class:`Chunk` instances ordered by distance.

        Raises:
            ValueError: If the similarity matrix has not been
                initialised.
        """
        self._check_infra()
        if self.similarity_matrix is None:
            raise ValueError("Similarity matrix not initialized.")
        k = top_k if top_k is not None else self._top_k
        query_embedding = self.embedding_model.encode(query)
        distances = pairwise_distances(
            query_embedding.reshape(1, -1),
            self.similarity_matrix,
            metric=self.similarity_metric,
        )[0]
        top_indices = np.argsort(distances)[:k]
        results = []
        for idx in top_indices:
            chunk_id = self.matrix_row_to_chunk_id[idx]
            doc_id, chunk_key = self._chunk_key_by_id[chunk_id]
            results.append(self.chunks[doc_id][chunk_key])
        return results

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score a set of chunk IDs against the query.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted by distance.

        Raises:
            ValueError: If the similarity matrix has not been
                initialised.
        """
        self._check_infra()
        if self.similarity_matrix is None:
            raise ValueError("Similarity matrix not initialized.")
        query_embedding = self.embedding_model.encode(query)
        chunk_id_to_row = {
            self.matrix_row_to_chunk_id[r]: r for r in self.matrix_row_to_chunk_id
        }
        valid_ids = [cid for cid in chunk_ids if cid in chunk_id_to_row]
        if not valid_ids:
            return []
        rows = [chunk_id_to_row[cid] for cid in valid_ids]
        distances = pairwise_distances(
            query_embedding.reshape(1, -1),
            self.similarity_matrix[rows],
            metric=self.similarity_metric,
        )[0]
        scored = list(zip(valid_ids, distances.tolist(), strict=True))
        scored.sort(key=lambda x: x[1])
        return scored

    def get_chunk_vectors(self, chunk_ids: List[int]) -> np.ndarray:
        """Return embedding vectors for the given chunk IDs.

        Args:
            chunk_ids: List of chunk IDs whose vectors are needed.

        Returns:
            A 2D numpy array of embedding vectors.

        Raises:
            ValueError: If the similarity matrix has not been
                initialised, or none of the chunk IDs are found.
        """
        if self.similarity_matrix is None:
            raise ValueError("Similarity matrix not initialized.")
        chunk_id_to_row: Dict[int, int] = {
            self.matrix_row_to_chunk_id[r]: r for r in self.matrix_row_to_chunk_id
        }
        rows = []
        for cid in chunk_ids:
            row = chunk_id_to_row.get(cid)
            if row is not None:
                rows.append(row)
        if not rows:
            raise ValueError(
                f"None of the provided chunk_ids {chunk_ids} were found "
                "in the similarity matrix."
            )
        return self.similarity_matrix[rows]
