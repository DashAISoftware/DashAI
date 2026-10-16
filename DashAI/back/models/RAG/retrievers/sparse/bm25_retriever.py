import logging
import os
import pickle
from typing import Dict, List, Tuple

import numpy as np
from scipy.sparse import lil_matrix
from sklearn.metrics.pairwise import pairwise_distances

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever

log = logging.getLogger(__name__)


class BM25RetrieverSchema(BaseSchema):
    """Schema for :class:`BM25Retriever`.

    Attributes:
        vectorizer: Word counter whose counts BM25 weights.
        k1: BM25 term frequency saturation parameter.
        b: BM25 length normalisation parameter.
        delta: BM25 IDF smoothing parameter.
        similarity_function: Distance metric for vector comparison.
        top_k: Number of chunks to select.
    """

    vectorizer: schema_field(
        component_field(parent="BagOfWordsConverter"),
        placeholder={
            "component": "BagOfWordsConverter",
            "params": {"max_features": None},
        },
        description=MultilingualString(
            en="Word counter whose counts BM25 weights.",
            es="Contador de palabras cuyos conteos pondera BM25.",
            pt="Contador de palavras cujas contagens o BM25 pondera.",
            de="Wortzähler, dessen Zählungen BM25 gewichtet.",
            zh="由 BM25 加权其计数的词频统计器。",
        ),
    )  # type: ignore

    k1: schema_field(
        float_field(ge=0.0),
        placeholder=1.5,
        description=MultilingualString(
            en="BM25 k1 parameter: term frequency saturation.",
            es="Parámetro k1 de BM25: saturación de frecuencia de término.",
            pt="Parâmetro k1 do BM25: saturação de frequência de termo.",
            de="BM25-k1-Parameter: Sättigung der Termhäufigkeit.",
            zh="BM25 k1 参数：词频饱和度。",
        ),
    )  # type: ignore

    b: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.75,
        description=MultilingualString(
            en="BM25 b parameter: length normalization.",
            es="Parámetro b de BM25: normalización de longitud.",
            pt="Parâmetro b do BM25: normalização de comprimento.",
            de="BM25-b-Parameter: Längennormalisierung.",
            zh="BM25 b 参数：长度归一化。",
        ),
    )  # type: ignore

    delta: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description=MultilingualString(
            en="BM25 delta parameter for IDF smoothing.",
            es="Parámetro delta de BM25 para suavizado de IDF.",
            pt="Parâmetro delta do BM25 para suavização de IDF.",
            de="BM25-delta-Parameter zur IDF-Glättung.",
            zh="用于 IDF 平滑的 BM25 delta 参数。",
        ),
    )  # type: ignore

    similarity_function: schema_field(
        enum_field(["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"]),
        placeholder="cosine",
        description=MultilingualString(
            en="Distance metric for comparing BM25-weighted vectors.",
            es="Métrica de distancia para comparar vectores ponderados BM25.",
            pt="Métrica de distância para comparar vetores ponderados por BM25.",
            de="Distanzmetrik zum Vergleichen BM25-gewichteter Vektoren.",
            zh="用于比较 BM25 加权向量的距离度量。",
        ),
    )  # type: ignore

    top_k: schema_field(
        int_field(ge=1),
        placeholder=5,
        description=MultilingualString(
            en="Number of chunks to select.",
            es="Número de fragmentos a seleccionar.",
            pt="Número de fragmentos a selecionar.",
            de="Anzahl der auszuwählenden Chunks.",
            zh="要选择的块数量。",
        ),
    )  # type: ignore


class BM25Retriever(SparseRetriever):
    """Sparse retriever using BM25 (Okapi) ranking for document retrieval.

    Computes BM25-weighted term-frequency vectors and retrieves via
    pairwise distance.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="BM25 Retriever",
        es="Recuperador BM25",
        pt="Recuperador BM25",
        de="BM25-Retriever",
        zh="BM25 检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Sparse retriever using BM25 (Okapi) ranking for document retrieval.",
        es="Recuperador disperso que usa ranking BM25 (Okapi) para"
        " recuperar documentos.",
        pt="Recuperador disperso que usa ranqueamento BM25 (Okapi) para"
        " recuperar documentos.",
        de="Sparser Retriever, der das BM25-Ranking (Okapi) zur"
        " Dokumentabfrage verwendet.",
        zh="使用 BM25（Okapi）排序进行文档检索的稀疏检索器。",
    )

    SCHEMA = BM25RetrieverSchema

    def __init__(self, **kwargs):
        """Initialize the BM25 retriever.

        Args:
            **kwargs: Must contain ``vectorizer``, ``k1``, ``b``,
                ``delta``, ``similarity_function``, and ``top_k``.
        """
        super().__init__(**kwargs)

        self.k1 = self.params.pop("k1")
        self.b = self.params.pop("b")
        self.delta = self.params.pop("delta")
        self.similarity_function_name = self.params.pop("similarity_function")
        self._top_k = self.params.pop("top_k")

        self._converter = self.params.pop("vectorizer")

    def init_model(self) -> None:
        """Restore saved state or fit BM25 from scratch."""
        if not self.load():
            self._fit()
        self._chunk_lookup = self._chunks_by_id()

    def load(self) -> bool:
        """Load a previously saved BM25 state from disk.

        Returns:
            ``True`` if state was loaded successfully, ``False`` if
            no saved state exists or loading failed.
        """
        if self._persistence.model_dir is None:
            return False
        model_dir = self._persistence.model_dir
        try:
            with open(os.path.join(model_dir, "bm25_vectorizer.pkl"), "rb") as f:
                vectorizer = pickle.load(f)
            with open(os.path.join(model_dir, "bm25_tf_matrix.pkl"), "rb") as f:
                tf_matrix = pickle.load(f)
            with open(os.path.join(model_dir, "bm25_matrix.pkl"), "rb") as f:
                bm25_matrix = pickle.load(f)
            with open(os.path.join(model_dir, "bm25_row_to_chunk_id.pkl"), "rb") as f:
                matrix_row_to_chunk_id = pickle.load(f)
            self._converter.vectorizer = vectorizer
            self._converter.fitted = True
            self._tf_matrix = tf_matrix
            self._bm25_matrix = bm25_matrix
            self.matrix_row_to_chunk_id = matrix_row_to_chunk_id
            return True
        except Exception as e:
            log.error("Error loading BM25 state: %s", e)
            return False

    def save(self) -> None:
        """Persist the vectorizer, matrices, and row to chunk id map to disk.

        Raises:
            ValueError: If ``persistence.model_dir`` is ``None``.
        """
        model_dir = self._persistence.model_dir
        if model_dir is None:
            raise ValueError(
                "Cannot save BM25Retriever: persistence.model_dir is None."
            )
        os.makedirs(model_dir, exist_ok=True)
        to_save = {
            "bm25_vectorizer.pkl": self._converter.vectorizer,
            "bm25_tf_matrix.pkl": self._tf_matrix,
            "bm25_matrix.pkl": self._bm25_matrix,
            "bm25_row_to_chunk_id.pkl": self.matrix_row_to_chunk_id,
        }
        for fname, obj in to_save.items():
            with open(os.path.join(model_dir, fname), "wb") as f:
                pickle.dump(obj, f)

    def _fit(self):
        """Count the words of every chunk and compute the BM25-weighted matrix."""
        chunk_texts = []
        current_idx = 0
        self.matrix_row_to_chunk_id: Dict[int, int] = {}

        for doc_chunks in self.chunks.values():
            for chunk in doc_chunks.values():
                chunk_texts.append(chunk.text)
                self.matrix_row_to_chunk_id[current_idx] = chunk.id
                current_idx += 1

        self._tf_matrix = self._converter.fit_matrix(chunk_texts)

        tf = self._tf_matrix.copy()
        n_docs = tf.shape[0]
        doc_lengths = np.array(tf.sum(axis=1)).flatten()
        avgdl = np.mean(doc_lengths)

        doc_freq = np.array((tf > 0).sum(axis=0)).flatten()
        idf = np.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
        idf += self.delta
        idf[idf < 0] = 0

        bm25 = lil_matrix(tf.shape)
        for i in range(tf.shape[0]):
            row = tf[i]
            length_norm = 1 - self.b + self.b * (doc_lengths[i] / avgdl)
            for j in range(row.indptr[0], row.indptr[1]):
                col = row.indices[j]
                tf_val = row.data[j]
                numerator = tf_val * (self.k1 + 1)
                denominator = tf_val + self.k1 * length_norm
                bm25[i, col] = idf[col] * numerator / denominator

        self._bm25_matrix = bm25.tocsr()

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k value.

        Returns:
            Number of chunks to retrieve.
        """
        return self._top_k

    def retrieve(self, query: str, top_k: int | None = None) -> List[Chunk]:
        """Retrieve the top-k chunks by BM25-weighted similarity.

        Args:
            query: The search query string.
            top_k: Override for the default ``top_k``. Uses the
                configured value if ``None``.

        Returns:
            A list of :class:`Chunk` instances ordered by distance.
        """
        self._check_infra()
        k = top_k if top_k is not None else self._top_k
        query_vec = self._converter.transform_matrix([query])
        distances = pairwise_distances(
            query_vec,
            self._bm25_matrix,
            metric=self.similarity_function_name,
        ).flatten()
        top_indices = np.argsort(distances)[:k]
        return [
            self._chunk_lookup[self.matrix_row_to_chunk_id[idx]] for idx in top_indices
        ]

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score a set of chunk IDs against the query.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted by distance.
        """
        self._check_infra()
        query_vec = self._converter.transform_matrix([query])
        chunk_id_to_row = {
            chunk_id: row for row, chunk_id in self.matrix_row_to_chunk_id.items()
        }
        rows, valid_ids = [], []
        for cid in chunk_ids:
            row = chunk_id_to_row.get(cid)
            if row is not None:
                rows.append(row)
                valid_ids.append(cid)
        if not rows:
            return []
        chunk_vectors = self._bm25_matrix[rows]
        distances = pairwise_distances(
            query_vec,
            chunk_vectors,
            metric=self.similarity_function_name,
        ).flatten()
        scored = list(zip(valid_ids, distances.tolist(), strict=True))
        scored.sort(key=lambda x: x[1])
        return scored

    def get_chunk_vectors(self, chunk_ids: List[int]) -> np.ndarray:
        """Return the BM25-weighted vectors for the given chunk IDs.

        Args:
            chunk_ids: List of chunk IDs whose vectors are needed.

        Returns:
            A 2D numpy array of BM25-weighted vectors.

        Raises:
            ValueError: If none of the provided chunk IDs are found in
                the matrix.
        """
        chunk_id_to_row = {
            chunk_id: row for row, chunk_id in self.matrix_row_to_chunk_id.items()
        }
        rows = []
        for cid in chunk_ids:
            row = chunk_id_to_row.get(cid)
            if row is not None:
                rows.append(row)
        if not rows:
            raise ValueError(
                f"None of the provided chunk_ids {chunk_ids} were found "
                "in the BM25 matrix."
            )
        return self._bm25_matrix[rows].toarray()
