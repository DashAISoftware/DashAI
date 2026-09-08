import logging
import os
import pickle
from typing import Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import pairwise_distances

from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    Lte,
    bool_field,
    component_field,
    enum_field,
    float_field,
    int_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever

log = logging.getLogger(__name__)


class TFIDFVectorizerSchema(BaseSchema):
    """Schema for the TF-IDF vectorizer parameters.

    Note:
        ``"None"`` is used as a string value instead of ``none_type()``
        because the current schema fields system does not support nullable
        enum types. The value is converted to Python ``None`` in
        :meth:`TFIDFVectorizerModel.__init__`.
    """

    strip_accents: schema_field(
        enum_field(enum=["ascii", "unicode", "None"]),
        placeholder="None",
        description=MultilingualString(
            en="Whether to strip accents from the text.",
            es="Si se deben eliminar los acentos del texto.",
            pt="Se devem ser removidos os acentos do texto.",
            de="Ob Akzente aus dem Text entfernt werden sollen.",
            zh="是否从文本中移除重音符号。",
        ),
    )  # type: ignore

    lowercase: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether to convert all characters to lowercase.",
            es="Si se deben convertir todos los caracteres a minúsculas.",
            pt="Se todos os caracteres devem ser convertidos para minúsculas.",
            de="Ob alle Zeichen in Kleinbuchstaben umgewandelt werden sollen.",
            zh="是否将所有字符转换为小写。",
        ),
    )  # type: ignore

    analyzer: schema_field(
        enum_field(enum=["word", "char", "char_wb"]),
        placeholder="word",
        description=MultilingualString(
            en="Whether the feature should be made of word or character n-grams.",
            es="Si las características deben ser n-gramas de palabras o caracteres.",
            pt="Se as características devem ser compostas de n-gramas de"
            " palavras ou caracteres.",
            de="Ob das Merkmal aus Wort- oder Zeichen-n-Grammen bestehen soll.",
            zh="特征是否应由词或字符 n-gram 构成。",
        ),
    )  # type: ignore

    stop_words: schema_field(
        list_field(string_field(), min_items=0),
        placeholder=[],
        description=MultilingualString(
            en="List of stop words. Leave empty to use none.",
            es="Lista de palabras vacías. Dejar vacío para no usar ninguna.",
            pt="Lista de palavras de parada (stop words). Deixe vazio para"
            " não usar nenhuma.",
            de="Liste der Stoppwörter. Leer lassen, um keine zu verwenden.",
            zh="停用词列表。留空则不使用。",
        ),
    )  # type: ignore

    ngram_range: schema_field(
        list_field(int_field(), min_items=2, max_items=2),
        placeholder=[1, 1],
        description=MultilingualString(
            en="Lower and upper boundary of the n-gram range.",
            es="Límite inferior y superior del rango de n-gramas.",
            pt="Limite inferior e superior do intervalo de n-gramas.",
            de="Untere und obere Grenze des n-Gramm-Bereichs.",
            zh="n-gram 范围的下限和上限。",
        ),
    )  # type: ignore

    max_df: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=1.0,
        description=MultilingualString(
            en="Ignore terms with document frequency above this threshold.",
            es="Ignorar términos con frecuencia de documento superior a este umbral.",
            pt="Ignorar termos com frequência de documento acima deste limite.",
            de="Begriffe mit einer Dokumentfrequenz über diesem Schwellenwert"
            " ignorieren.",
            zh="忽略文档频率高于此阈值的词项。",
        ),
    )  # type: ignore

    min_df: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.0,
        description=MultilingualString(
            en="Ignore terms with document frequency below this threshold.",
            es="Ignorar términos con frecuencia de documento inferior a este umbral.",
            pt="Ignorar termos com frequência de documento abaixo deste limite.",
            de="Begriffe mit einer Dokumentfrequenz unter diesem Schwellenwert"
            " ignorieren.",
            zh="忽略文档频率低于此阈值的词项。",
        ),
    )  # type: ignore

    max_features: schema_field(
        int_field(ge=0),
        placeholder=1000,
        description=MultilingualString(
            en="Maximum number of features. 0 means no limit.",
            es="Número máximo de características. 0 significa sin límite.",
            pt="Número máximo de características. 0 significa sem limite.",
            de="Maximale Anzahl von Merkmalen. 0 bedeutet kein Limit.",
            zh="最大特征数量。0 表示无限制。",
        ),
    )  # type: ignore

    norm: schema_field(
        enum_field(enum=["l1", "l2", "None"]),
        placeholder="l2",
        description=MultilingualString(
            en="Norm used to normalize term vectors.",
            es="Norma utilizada para normalizar los vectores de términos.",
            pt="Norma usada para normalizar os vetores de termos.",
            de="Norm zum Normalisieren der Termvektoren.",
            zh="用于归一化词向量的范数。",
        ),
    )  # type: ignore

    use_idf: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Enable inverse-document-frequency reweighting.",
            es="Activar reponderación por frecuencia inversa de documento.",
            pt="Ativar reponderação por frequência inversa de documento.",
            de="Neugewichtung über die inverse Dokumentfrequenz aktivieren.",
            zh="启用逆文档频率加权。",
        ),
    )  # type: ignore

    smooth_idf: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Smooth IDF weights to prevent zero divisions.",
            es="Suavizar pesos IDF para prevenir divisiones por cero.",
            pt="Suavizar pesos IDF para evitar divisões por zero.",
            de="IDF-Gewichte glätten, um Divisionen durch Null zu vermeiden.",
            zh="平滑 IDF 权重以防止除零。",
        ),
    )  # type: ignore

    sublinear_tf: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en="Apply sublinear TF scaling (1 + log(tf)).",
            es="Aplicar escalado sublineal de TF (1 + log(tf)).",
            pt="Aplicar escalonamento sublinear de TF (1 + log(tf)).",
            de="Sublineare TF-Skalierung anwenden (1 + log(tf)).",
            zh="应用亚线性 TF 缩放（1 + log(tf)）。",
        ),
    )  # type: ignore

    # A range the underlying library takes as one tuple, which the schema
    # cannot express, so it is split into two fields. sklearn raises "max_df corresponds
    # to < documents than min_df"; equal proportions are fine.
    rules = [
        Check(
            Lte("min_df", "max_df"),
            id="tfidf.document_frequency_is_ordered",
            targets=["min_df", "max_df"],
            message=MultilingualString(
                en="The minimum document frequency cannot be greater than the maximum.",
                es=(
                    "La frecuencia mínima de documento no puede ser mayor que la "
                    "máxima."
                ),
                pt="A frequência mínima de documento não pode ser maior que a máxima.",
                de=(
                    "Die minimale Dokumentfrequenz darf nicht größer als die maximale "
                    "sein."
                ),
                zh="最小文档频率不能大于最大值。",
            ),
        ),
    ]


class TFIDFVectorizerModel(BaseModel):
    """Model component that encapsulates a :class:`TfidfVectorizer`.

    Validates parameters against :class:`TFIDFVectorizerSchema` and
    constructs the underlying scikit-learn vectorizer.
    """

    SCHEMA = TFIDFVectorizerSchema
    DISPLAY_NAME: str = MultilingualString(
        en="TF-IDF Vectorizer Model",
        es="Modelo de Vectorización TF-IDF",
        pt="Modelo de Vectorização TF-IDF",
        de="TF-IDF-Vectorizer-Modell",
        zh="TF-IDF 向量化器模型",
    )
    DESCRIPTION: str = MultilingualString(
        en="Model component that encapsulates a TF-IDF vectorizer.",
        es="Componente del modelo que encapsula un vectorizador TF-IDF.",
        pt="Componente do modelo que encapsula um vectorizador TF-IDF.",
        de="Modellkomponente, die einen TF-IDF-Vectorizer kapselt.",
        zh="封装 TF-IDF 向量化器的模型组件。",
    )

    def __init__(self, **kwargs) -> None:
        """Initialize and build the underlying ``TfidfVectorizer``.

        Args:
            **kwargs: Parameters matching :class:`TFIDFVectorizerSchema`.
        """
        validated = self.SCHEMA.model_validate(kwargs)
        self.params = dict(validated)
        if self.params.get("strip_accents") == "None":
            self.params["strip_accents"] = None
        stop_words = self.params.get("stop_words") or None
        ngram_range = tuple(self.params.get("ngram_range"))
        self.model = TfidfVectorizer(
            strip_accents=self.params.get("strip_accents"),
            lowercase=self.params.get("lowercase"),
            analyzer=self.params.get("analyzer"),
            stop_words=stop_words,
            ngram_range=ngram_range,
            max_df=self.params.get("max_df"),
            min_df=self.params.get("min_df"),
            max_features=self.params.get("max_features"),
            norm=self.params.get("norm"),
            use_idf=self.params.get("use_idf"),
            smooth_idf=self.params.get("smooth_idf"),
            sublinear_tf=self.params.get("sublinear_tf"),
        )

    def save(self, filename: str = "") -> None:
        """No-op save (state managed by the parent retriever).

        Args:
            filename: Ignored.
        """

    def load(self, filename: str = "") -> None:
        """No-op load (state managed by the parent retriever).

        Args:
            filename: Ignored.
        """

    def train(self, **kwargs):
        """No-op train (fitting is done by the parent retriever).

        Args:
            **kwargs: Ignored.
        """
        return


class TFIDFRetrieverSchema(BaseSchema):
    """Schema for :class:`TFIDFRetriever`.

    Attributes:
        TFIDFVectorizer: Parameters for the TF-IDF vectorizer component.
        similarity_function: Distance metric for vector comparison.
        top_k: Number of chunks to select.
    """

    TFIDFVectorizer: schema_field(
        component_field(parent="TFIDFVectorizerModel"),
        placeholder={"component": "TFIDFVectorizerModel", "params": {}},
        description=MultilingualString(
            en="TF-IDF Vectorizer parameters.",
            es="Parámetros del vectorizador TF-IDF.",
            pt="Parâmetros do vectorizador TF-IDF.",
            de="TF-IDF-Vectorizer-Parameter.",
            zh="TF-IDF 向量化器参数。",
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
            **kwargs: Must contain ``TFIDFVectorizer``,
                ``similarity_function``, and ``top_k``.
        """
        super().__init__(**kwargs)

        vectorizer_model = self.params.pop("TFIDFVectorizer")
        self._vectorizer = vectorizer_model.model
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
            self._vectorizer = vectorizer
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
            "tfidf_vectorizer.pkl": self._vectorizer,
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

        self._tf_idf_matrix = self._vectorizer.fit_transform(chunk_texts)

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
        query_vector = self._vectorizer.transform([query])
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
        query_vector = self._vectorizer.transform([query])
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
