from typing import Any, Dict, Optional

from DashAI.back.converters.scikit_learn.text_vectorizer import (
    SparseTextVectorizer,
    TextVectorizerSchema,
    vectorizer_options,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Integer, Text


class BagOfWordsConverterSchema(TextVectorizerSchema):
    """Options of the bag of words converter."""


class BagOfWordsConverter(SparseTextVectorizer):
    """Convert raw text documents into a matrix of token occurrence counts.

    The Bag-of-Words (BoW) model represents each document as a fixed length
    vector of word counts, discarding word order and grammar. During ``fit``
    a vocabulary of up to ``max_features`` terms is built from the training
    corpus. During ``transform`` each document is mapped to that vocabulary,
    producing one integer-valued column per token.

    Optional preprocessing steps include lower-casing, stop-word removal, and
    n-gram extraction (unigrams, bigrams, …). The result is a sparse integer
    matrix converted to a DashAI dataset with one column per vocabulary term.

    Internally wraps ``sklearn.feature_extraction.text.CountVectorizer``.

    The BoW representation is one of the foundational techniques in information
    retrieval described in Salton & McGill (1983) [2].

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html
    - [2] Salton, G. & McGill, M. J. (1983). Introduction to Modern Information
        Retrieval. McGraw-Hill.
    """

    SCHEMA = BagOfWordsConverterSchema
    DISPLAY_NAME = MultilingualString(
        en="Bag of Words",
        es="Bolsa de Palabras",
        pt="Bag of Words",
        de="Bag of Words",
        zh="词袋模型",
    )
    COLUMN_PREFIX = "bow_"
    COLUMN_DTYPE = "int64"
    IMAGE_PREVIEW = "bag_of_words.png"

    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
    }
    DESCRIPTION = MultilingualString(
        en=(
            "Converts text into a Bag-of-Words representation with one column "
            "per token (frequency per token)."
        ),
        es=(
            "Convierte texto en una representación de Bolsa de Palabras con una "
            "columna por token (frecuencia por token)."
        ),
        pt=(
            "Converte texto em uma representação Bag of Words com uma coluna "
            "por token (frequência por token)."
        ),
        de=(
            "Konvertiert Text in eine Bag-of-Words-Darstellung mit einer Spalte "
            "pro Token (Häufigkeit pro Token)."
        ),
        zh="将文本转换为词袋模型表示，每个词元对应一列（每词元的频率）。",
    )

    def build_vectorizer(self, params: Dict[str, Any]) -> Any:
        """Return an unfitted ``CountVectorizer``.

        Parameters
        ----------
        params : dict
            Converter parameters.

        Returns
        -------
        CountVectorizer
            The configured vectorizer.
        """
        from sklearn.feature_extraction.text import CountVectorizer

        return CountVectorizer(**vectorizer_options(params))

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        The output of this converter is a set of integer columns, one per
        vocabulary term, containing the raw token frequency counts produced
        by ``CountVectorizer``.

        Parameters
        ----------
        column_name : str, optional
            The column name to look up in the fitted vectoriser. When provided
            and the vectoriser has been fitted, the returned type reflects the
            actual fitted vocabulary. Defaults to None.

        Returns
        -------
        DashAIDataType
            An Integer type for each token frequency column.
        """
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())
