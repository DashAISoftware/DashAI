from typing import TYPE_CHECKING, Optional

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    Lte,
    bool_field,
    enum_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Integer, Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BagOfWordsConverterSchema(BaseSchema):
    """Schema for configuring the BagOfWordsConverter.

    Wraps ``sklearn.feature_extraction.text.CountVectorizer`` and exposes
    vocabulary size, casing, stop-word removal, and n-gram range as schema
    fields validated before being forwarded to the underlying scikit-learn
    estimator.
    """

    max_features: schema_field(
        int_field(gt=0),
        placeholder=1000,
        description=MultilingualString(
            en="Maximum number of features (most frequent words) to keep.",
            es=(
                "Número máximo de características (palabras más frecuentes) "
                "a conservar."
            ),
            pt=(
                "Número máximo de características (palavras mais frequentes) a manter."
            ),
            de="Maximale Anzahl der beizubehaltenden Merkmale (häufigste Wörter).",
            zh="保留的最大特征数（最常见的词）。",
        ),
    )  # type: ignore
    lowercase: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether to convert all characters to lowercase before tokenizing.",
            es="Si se debe convertir todo a minúsculas antes de tokenizar.",
            pt=(
                "Se todos os caracteres devem ser convertidos para "
                "minúsculas antes de tokenizar."
            ),
            de=(
                "Ob alle Zeichen vor der Tokenisierung in Kleinbuchstaben umgewandelt "
                "werden sollen."
            ),
            zh="是否在分词前将所有字符转换为小写。",
        ),
    )  # type: ignore
    stop_words: schema_field(
        none_type(enum_field(["english"])),
        placeholder=None,
        description=MultilingualString(
            en="Stop word set to remove. Use 'english' or None.",
            es="Conjunto de stopwords a eliminar. Usa 'english' o None.",
            pt="Conjunto de stopwords a remover. Use 'english' ou None.",
            de="Stoppwort-Set zum Entfernen. Verwende 'english' oder None.",
            zh="要删除的停用词集。使用 'english' 或 None。",
        ),
    )  # type: ignore
    lower_bound_ngrams: schema_field(
        int_field(gt=0, le=5),
        placeholder=1,
        description=MultilingualString(
            en="Lower bound for n-grams. Must be <= upper bound.",
            es="Límite inferior de n-grams. Debe ser <= al límite superior.",
            pt="Limite inferior para n-grams. Deve ser <= ao limite superior.",
            de="Untergrenze für N-Gramme. Muss <= Obergrenze sein.",
            zh="n-gram 的下界。必须 <= 上界。",
        ),
    )  # type: ignore
    upper_bound_ngrams: schema_field(
        int_field(gt=0, le=5),
        placeholder=1,
        description=MultilingualString(
            en="Upper bound for n-grams. Must be >= lower bound.",
            es="Límite superior de n-grams. Debe ser >= al límite inferior.",
            pt="Limite superior para n-grams. Deve ser >= ao limite inferior.",
            de="Obergrenze für N-Gramme. Muss >= Untergrenze sein.",
            zh="n-gram 的上界。必须 >= 下界。",
        ),
    )  # type: ignore

    # A range the underlying library takes as one tuple, which the schema
    # cannot express, so it is split into two fields. sklearn: "Invalid value for
    # ngram_range ... lower boundary larger than upper"; equal is fine.
    rules = [
        Check(
            Lte("lower_bound_ngrams", "upper_bound_ngrams"),
            id="bag_of_words.ngram_range_is_ordered",
            targets=["lower_bound_ngrams", "upper_bound_ngrams"],
            message=MultilingualString(
                en="The lower n-gram bound cannot be greater than the upper bound.",
                es=(
                    "El límite inferior de n-gramas no puede ser mayor que el límite "
                    "superior."
                ),
                pt=(
                    "O limite inferior de n-gramas não pode ser maior que o limite "
                    "superior."
                ),
                de=(
                    "Die untere n-Gramm-Grenze darf nicht größer als die obere Grenze "
                    "sein."
                ),
                zh="n元语法下界不能大于上界。",
            ),
        ),
    ]


class BagOfWordsConverter(AdvancedPreprocessingConverter, BaseConverter):
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

    def __init__(self, **kwargs):
        """Initialise the bag-of-words converter and configure the vectorizer.

        Parameters
        ----------
        **kwargs : dict
            max_features : int, optional
                Maximum vocabulary size. Default ``1000``.
            lowercase : bool, optional
                Convert all text to lowercase before tokenizing. Default ``True``.
            stop_words : str or list, optional
                Stop-word list to remove. Default ``"english"``.
            lower_bound_ngrams : int, optional
                Minimum n-gram size. Default ``1``.
            upper_bound_ngrams : int, optional
                Maximum n-gram size. Default ``1``.
        """
        super().__init__()
        from sklearn.feature_extraction.text import CountVectorizer

        self.vectorizer = CountVectorizer(
            max_features=kwargs.get("max_features", 1000),
            lowercase=kwargs.get("lowercase", True),
            stop_words=kwargs.get("stop_words"),
            ngram_range=(
                kwargs.get("lower_bound_ngrams", 1),
                kwargs.get("upper_bound_ngrams", 1),
            ),
        )
        self.fitted = False

    def fit(self, x: "DashAIDataset", y=None) -> "BagOfWordsConverter":
        """Fit CountVectorizer on the first text column of the dataset.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset. Only the first column is used for fitting.
        y : ignored
            Present for API compatibility.

        Returns
        -------
        BagOfWordsConverter
            The fitted converter instance (``self``).
        """
        X_df = x.to_pandas()
        texts = X_df.iloc[:, 0].astype(str)
        self.vectorizer.fit(texts)
        self.fitted = True
        return self

    def transform(self, x: "DashAIDataset", y=None) -> "DashAIDataset":
        """Transform text into Bag-of-Words token frequency columns.

        Appends one ``bow_<token>`` column per vocabulary term to the original
        dataset. The source text column is preserved unchanged.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset. The first column is vectorised.
        y : ignored
            Present for API compatibility.

        Returns
        -------
        DashAIDataset
            Original dataset with ``bow_*`` token frequency columns appended.

        Raises
        ------
        RuntimeError
            If :meth:`fit` has not been called yet.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if not self.fitted:
            raise RuntimeError("The converter must be fitted before calling transform.")

        X_df = x.to_pandas()
        texts = X_df.iloc[:, 0].astype(str)

        bow_matrix = self.vectorizer.transform(texts)
        feature_names = self.vectorizer.get_feature_names_out()
        output_type = self.get_output_type()

        combined_table = x.arrow_table
        combined_types = dict(x.types)

        bow_array = bow_matrix.toarray()
        for i, token in enumerate(feature_names):
            prefixed = f"bow_{token}"
            combined_table = combined_table.append_column(
                prefixed, pa.array(bow_array[:, i].tolist(), type=pa.int64())
            )
            combined_types[prefixed] = output_type

        return DashAIDataset(combined_table, types=combined_types, splits=x.splits)

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
