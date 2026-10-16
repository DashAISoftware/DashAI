from typing import Any, Dict, Optional

from DashAI.back.converters.scikit_learn.text_vectorizer import (
    SparseTextVectorizer,
    TextVectorizerSchema,
    vectorizer_options,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Text


class TFIDFConverterSchema(TextVectorizerSchema):
    """Options of the TF-IDF converter: the shared vectorizer options plus the
    TF-IDF weighting."""

    norm: schema_field(
        none_type(enum_field(["l1", "l2"])),
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


class TFIDFConverter(SparseTextVectorizer):
    """Convert raw text documents into a matrix of TF-IDF weighted features.

    TF-IDF (Term Frequency - Inverse Document Frequency) re-weights raw token
    counts so that terms that appear frequently in a specific document but
    rarely across the whole corpus receive a higher score, while common
    stop-like terms are down-weighted. Each document is represented as a
    floating-point vector of TF-IDF scores, one dimension per vocabulary term.

    The TF-IDF score for term *t* in document *d* is:

        tfidf(t, d) = tf(t, d) x log((1 + n) / (1 + df(t))) + 1

    where *n* is the total number of documents and *df(t)* is the number of
    documents containing *t* (scikit-learn's ``smooth_idf=True`` default).

    Optional preprocessing steps include lower-casing, stop-word removal, and
    n-gram extraction. The result is a floating-point DashAI dataset with one
    column per vocabulary term.

    Internally wraps ``sklearn.feature_extraction.text.TfidfVectorizer``.

    The TF-IDF weighting scheme was introduced as a core technique in
    information retrieval by Salton & McGill (1983) [2].

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
    - [2] Salton, G. & McGill, M. J. (1983). Introduction to Modern Information
        Retrieval. McGraw-Hill.
    """

    SCHEMA = TFIDFConverterSchema
    DISPLAY_NAME = MultilingualString(
        en="TF-IDF", es="TF-IDF", pt="TF-IDF", de="TF-IDF", zh="TF-IDF"
    )
    COLUMN_PREFIX = "tfidf_"
    COLUMN_DTYPE = "float64"
    IMAGE_PREVIEW = "tf_idf.png"

    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
    }
    DESCRIPTION = MultilingualString(
        en=(
            "Converts text into a TF-IDF representation with one column per "
            "token (TF-IDF weight per token)."
        ),
        es=(
            "Convierte texto en una representación TF-IDF con una columna por "
            "token (peso TF-IDF por token)."
        ),
        pt=(
            "Converte texto em uma representação TF-IDF com uma coluna por "
            "token (peso TF-IDF por token)."
        ),
        de=(
            "Konvertiert Text in eine TF-IDF-Darstellung mit einer Spalte pro "
            "Token (TF-IDF-Gewicht pro Token)."
        ),
        zh="将文本转换为 TF-IDF 表示，每个词元对应一列（每词元的 TF-IDF 权重）。",
    )

    def build_vectorizer(self, params: Dict[str, Any]) -> Any:
        """Return an unfitted ``TfidfVectorizer``.

        Parameters
        ----------
        params : dict
            Converter parameters.

        Returns
        -------
        TfidfVectorizer
            The configured vectorizer.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        return TfidfVectorizer(
            **vectorizer_options(params),
            norm=params.get("norm", "l2"),
            use_idf=params.get("use_idf", True),
            smooth_idf=params.get("smooth_idf", True),
            sublinear_tf=params.get("sublinear_tf", False),
        )

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        The output of this converter is a set of float columns, one per
        vocabulary term, containing the TF-IDF weights produced by
        ``TfidfVectorizer``.

        Parameters
        ----------
        column_name : str, optional
            The column name to look up in the fitted vectoriser. When provided
            and the vectoriser has been fitted, the returned type reflects the
            actual fitted vocabulary. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Float type for each TF-IDF weight column.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
