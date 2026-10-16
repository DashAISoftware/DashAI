import logging
import os
import pickle
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import pairwise_distances

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever

log = logging.getLogger(__name__)


class TFIDFRetrieverSchema(BaseSchema):
    """Schema for :class:`TFIDFRetriever`.

    Attributes:
        vectorizer: The TF-IDF converter fitted on the chunks.
        similarity_function: Distance metric for vector comparison.
        top_k: Number of chunks to select.
    """

    vectorizer: schema_field(
        component_field(parent="TFIDFConverter"),
        placeholder={"component": "TFIDFConverter", "params": {"max_features": None}},
        description=MultilingualString(
            en="TF-IDF vectorizer fitted on the chunks.",
            es="Vectorizador TF-IDF ajustado sobre los fragmentos.",
            pt="Vetorizador TF-IDF ajustado sobre os fragmentos.",
            de="TF-IDF-Vektorisierer, der auf die Chunks angepasst wird.",
            zh="在文本块上拟合的 TF-IDF 向量化器。",
        ),
    )  # type: ignore

    similarity_function: schema_field(
        enum_field(["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"]),
        placeholder="cosine",
        description=MultilingualString(
            en="Distance metric for comparing TF-IDF vectors.",
            es="Métrica de distancia para comparar vectores TF-IDF.",
            pt="Métrica de distância para comparar vetores TF-IDF.",
            de="Distanzmetrik zum Vergleichen von TF-IDF-Vektoren.",
            zh="用于比较 TF-IDF 向量的距离度量。",
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


class TFIDFRetriever(SparseRetriever):
    """Sparse retriever using TF-IDF vectorization for document retrieval.

    Fits a :class:`sklearn.feature_extraction.text.TfidfVectorizer` on
    the injected chunks and retrieves via pairwise distance.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="TF-IDF Retriever",
        es="Recuperador TF-IDF",
        pt="Recuperador TF-IDF",
        de="TF-IDF-Retriever",
        zh="TF-IDF 检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Sparse retriever using TF-IDF vectorization for document retrieval.",
        es="Recuperador disperso que usa vectorización TF-IDF para"
        " recuperar documentos.",
        pt="Recuperador disperso que usa vetorização TF-IDF para recuperar documentos.",
        de="Sparser Retriever, der die TF-IDF-Vektorisierung zur"
        " Dokumentabfrage verwendet.",
        zh="使用 TF-IDF 向量化进行文档检索的稀疏检索器。",
    )

    SCHEMA = TFIDFRetrieverSchema

    def __init__(self, **kwargs):
        """Initialize the TF-IDF retriever.

        Args:
            **kwargs: Must contain ``vectorizer``,
                ``similarity_function``, and ``top_k``.
        """
        super().__init__(**kwargs)

        self._converter = self.params.pop("vectorizer")
        self.similarity_function_name = self.params.pop("similarity_function")
        self._top_k = self.params.pop("top_k")

    def init_model(self) -> None:
        """Restore saved state or fit the vectorizer from scratch."""
        if not self.load():
            self._fit()

    def load(self) -> bool:
        """Load a previously saved TF-IDF state from disk.

        Returns:
            ``True`` if state was loaded successfully, ``False`` if
            no saved state exists or loading failed.
        """
        if self._persistence.model_dir is None:
            return False
        model_dir = self._persistence.model_dir
        try:
            with open(os.path.join(model_dir, "tfidf_vectorizer.pkl"), "rb") as f:
                vectorizer = pickle.load(f)
            with open(os.path.join(model_dir, "tf_idf_matrix.pkl"), "rb") as f:
                tf_idf_matrix = pickle.load(f)
            with open(
                os.path.join(model_dir, "matrix_row_to_chunk_map.pkl"), "rb"
            ) as f:
                matrix_row_to_chunk_map = pickle.load(f)
            self._converter.vectorizer = vectorizer
            self._converter.fitted = True
            self._tf_idf_matrix = tf_idf_matrix
            self.matrix_row_to_chunk_map = matrix_row_to_chunk_map
            return True
        except Exception as e:
            log.error("Error loading TFIDF state: %s", e)
            return False

    def save(self) -> None:
        """Persist the vectorizer, TF-IDF matrix, and chunk map to disk.

        Raises:
            ValueError: If ``persistence.model_dir`` is ``None``.
        """
        model_dir = self._persistence.model_dir
        if model_dir is None:
            raise ValueError(
                "Cannot save TFIDFRetriever: persistence.model_dir is None."
            )
        os.makedirs(model_dir, exist_ok=True)
        to_save = {
            "tfidf_vectorizer.pkl": self._converter.vectorizer,
            "tf_idf_matrix.pkl": self._tf_idf_matrix,
            "matrix_row_to_chunk_map.pkl": self.matrix_row_to_chunk_map,
        }
        for fname, obj in to_save.items():
            with open(os.path.join(model_dir, fname), "wb") as f:
                pickle.dump(obj, f)

    def _fit(self):
        """Fit the TF-IDF vectorizer on all chunk texts and build the matrix."""
        chunk_texts = []
        current_idx = 0
        self.matrix_row_to_chunk_map: Dict[int, Chunk] = {}

        for doc_chunks in self.chunks.values():
            for chunk in doc_chunks.values():
                chunk_texts.append(chunk.text)
                self.matrix_row_to_chunk_map[current_idx] = chunk
                current_idx += 1

        self._tf_idf_matrix = self._converter.fit_matrix(chunk_texts)

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k value.

        Returns:
            Number of chunks to retrieve.
        """
        return self._top_k

    def retrieve(self, query: str, top_k: int | None = None) -> List[Chunk]:
        """Retrieve the top-k chunks by TF-IDF similarity.

        Args:
            query: The search query string.
            top_k: Override for the default ``top_k``. Uses the
                configured value if ``None``.

        Returns:
            A list of :class:`Chunk` instances ordered by distance.
        """
        self._check_infra()
        k = top_k if top_k is not None else self._top_k
        query_vector = self._converter.transform_matrix([query])
        distances = pairwise_distances(
            query_vector,
            self._tf_idf_matrix,
            metric=self.similarity_function_name,
        ).flatten()
        top_indices = np.argsort(distances)[:k]
        return [self.matrix_row_to_chunk_map[idx] for idx in top_indices]

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score a set of chunk IDs against the query.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted by distance.
        """
        self._check_infra()
        query_vector = self._converter.transform_matrix([query])
        chunk_id_to_row = {c.id: r for r, c in self.matrix_row_to_chunk_map.items()}
        rows, valid_ids = [], []
        for cid in chunk_ids:
            row = chunk_id_to_row.get(cid)
            if row is not None:
                rows.append(row)
                valid_ids.append(cid)
        if not rows:
            return []
        distances = pairwise_distances(
            query_vector,
            self._tf_idf_matrix[rows],
            metric=self.similarity_function_name,
        ).flatten()
        scored = list(zip(valid_ids, distances.tolist(), strict=True))
        scored.sort(key=lambda x: x[1])
        return scored

    def get_chunk_vectors(self, chunk_ids: List[int]) -> np.ndarray:
        """Return the TF-IDF vectors for the given chunk IDs.

        Args:
            chunk_ids: List of chunk IDs whose vectors are needed.

        Returns:
            A 2D numpy array of TF-IDF vectors.

        Raises:
            ValueError: If none of the provided chunk IDs are found in
                the matrix.
        """
        chunk_id_to_row = {c.id: r for r, c in self.matrix_row_to_chunk_map.items()}
        rows = []
        for cid in chunk_ids:
            row = chunk_id_to_row.get(cid)
            if row is not None:
                rows.append(row)
        if not rows:
            raise ValueError(
                f"None of the provided chunk_ids {chunk_ids} were found "
                "in the TF-IDF matrix."
            )
        return self._tf_idf_matrix[rows].toarray()
