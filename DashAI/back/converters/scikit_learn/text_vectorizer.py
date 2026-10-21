from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    Lte,
    bool_field,
    enum_field,
    float_field,
    int_field,
    list_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TextVectorizerSchema(BaseSchema):
    """Options shared by the TF-IDF and bag of words converters.

    They map to the arguments common to ``TfidfVectorizer`` and
    ``CountVectorizer``.
    """

    max_features: schema_field(
        none_type(int_field(gt=0)),
        placeholder=1000,
        description=MultilingualString(
            en=(
                "Maximum number of terms to keep, the most frequent first. "
                "Leave empty to keep every term."
            ),
            es=(
                "Número máximo de términos a conservar, los más frecuentes "
                "primero. Dejar vacío para conservar todos."
            ),
            pt=(
                "Número máximo de termos a manter, os mais frequentes primeiro. "
                "Deixe vazio para manter todos."
            ),
            de=(
                "Maximale Anzahl der beizubehaltenden Begriffe, die häufigsten "
                "zuerst. Leer lassen, um alle zu behalten."
            ),
            zh="保留的最大词项数，最常见的优先。留空则保留全部词项。",
        ),
    )  # type: ignore
    lowercase: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=("Whether to convert all characters to lowercase before tokenizing."),
            es=("Si se debe convertir todo a minúsculas antes de tokenizar."),
            pt=(
                "Se todos os caracteres devem ser convertidos para minúsculas "
                "antes de tokenizar."
            ),
            de=(
                "Ob alle Zeichen vor der Tokenisierung in Kleinbuchstaben umgewandelt "
                "werden sollen."
            ),
            zh="是否在分词前将所有字符转换为小写。",
        ),
    )  # type: ignore
    strip_accents: schema_field(
        none_type(enum_field(enum=["ascii", "unicode"])),
        placeholder=None,
        description=MultilingualString(
            en="Remove accents during preprocessing.",
            es="Eliminar acentos durante el preprocesamiento.",
            pt="Remover acentos durante o pré-processamento.",
            de="Akzente während der Vorverarbeitung entfernen.",
            zh="在预处理期间移除重音符号。",
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
    custom_stop_words: schema_field(
        none_type(list_field(string_field(), min_items=1)),
        placeholder=None,
        description=MultilingualString(
            en="Extra words to ignore, added to the stop word set above.",
            es="Palabras extra a ignorar, sumadas al conjunto de stopwords.",
            pt="Palavras extras a ignorar, somadas ao conjunto de stopwords.",
            de="Zusätzliche zu ignorierende Wörter, ergänzt zum Stoppwort-Set.",
            zh="额外要忽略的词，与上方停用词集合并。",
        ),
    )  # type: ignore
    lower_bound_ngrams: schema_field(
        int_field(gt=0, le=5),
        placeholder=1,
        description=MultilingualString(
            en=("Lower bound for n-grams to be extracted. Must be <= upper bound."),
            es=(
                "Límite inferior de n-grams a extraer. Debe ser <= al límite superior."
            ),
            pt=(
                "Limite inferior de n-grams a extrair. Deve ser <= ao limite superior."
            ),
            de="Untergrenze für zu extrahierende N-Gramme. Muss <= Obergrenze sein.",
            zh="要提取的 n-gram 下界。必须 <= 上界。",
        ),
    )  # type: ignore
    upper_bound_ngrams: schema_field(
        int_field(gt=0, le=5),
        placeholder=1,
        description=MultilingualString(
            en=("Upper bound for n-grams to be extracted. Must be >= lower bound."),
            es=(
                "Límite superior de n-grams a extraer. Debe ser >= al límite inferior."
            ),
            pt=(
                "Limite superior de n-grams a extrair. Deve ser >= ao limite inferior."
            ),
            de="Obergrenze für zu extrahierende N-Gramme. Muss >= Untergrenze sein.",
            zh="要提取的 n-gram 上界。必须 >= 下界。",
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

    rules = [
        Check(
            Lte("lower_bound_ngrams", "upper_bound_ngrams"),
            id="text_vectorizer.ngram_range_is_ordered",
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
        Check(
            Lte("min_df", "max_df"),
            id="text_vectorizer.document_frequency_is_ordered",
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


def vectorizer_options(params: Dict[str, Any]) -> Dict[str, Any]:
    """Map converter parameters to scikit-learn vectorizer arguments.

    Parameters
    ----------
    params : dict
        Converter parameters; missing keys take the schema placeholders.

    Returns
    -------
    dict
        Arguments shared by ``CountVectorizer`` and ``TfidfVectorizer``.
    """
    stop_words = params.get("stop_words")
    custom = list(params.get("custom_stop_words") or [])
    if stop_words == "english" and custom:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

        words: Any = sorted(set(ENGLISH_STOP_WORDS) | set(custom))
    elif custom:
        words = custom
    else:
        words = stop_words
    return {
        "max_features": params.get("max_features", 1000),
        "lowercase": params.get("lowercase", True),
        "strip_accents": params.get("strip_accents"),
        "analyzer": params.get("analyzer", "word"),
        "stop_words": words,
        "ngram_range": (
            params.get("lower_bound_ngrams", 1),
            params.get("upper_bound_ngrams", 1),
        ),
        "min_df": params.get("min_df", 0.0),
        "max_df": params.get("max_df", 1.0),
    }


class SparseTextVectorizer(AdvancedPreprocessingConverter):
    """Turn a text column into one column per term of a learned vocabulary.

    Retrievers call :meth:`fit_matrix` and :meth:`transform_matrix` and keep
    the sparse matrices. Dataset notebooks call :meth:`fit` and
    :meth:`transform`, which append one ``{COLUMN_PREFIX}{term}`` column per
    term to the dataset.
    """

    SCHEMA = TextVectorizerSchema
    COLUMN_PREFIX: str = ""
    COLUMN_DTYPE: str = "float64"
    metadata = {"allowed_types": [Text], "allowed_dtypes": []}

    def __init__(self, **kwargs: Any) -> None:
        """Build the scikit-learn vectorizer from the parameters.

        Parameters
        ----------
        **kwargs
            Parameters matching ``SCHEMA``.
        """
        super().__init__()
        self.params: Dict[str, Any] = dict(kwargs)
        self.vectorizer = self.build_vectorizer(self.params)
        self.fitted = False

    def build_vectorizer(self, params: Dict[str, Any]) -> Any:
        """Return the unfitted scikit-learn vectorizer.

        Parameters
        ----------
        params : dict
            Converter parameters.

        Returns
        -------
        Any
            A ``CountVectorizer`` or ``TfidfVectorizer``.
        """
        raise NotImplementedError

    def fit_matrix(self, texts: List[str]) -> Any:
        """Learn the vocabulary and return the matrix of the texts.

        Parameters
        ----------
        texts : list of str
            The corpus.

        Returns
        -------
        scipy.sparse.csr_matrix
            One row per text, one column per term.
        """
        matrix = self.vectorizer.fit_transform(texts)
        self.fitted = True
        return matrix.tocsr()

    def transform_matrix(self, texts: List[str]) -> Any:
        """Return the matrix of texts over the learned vocabulary.

        Parameters
        ----------
        texts : list of str
            Texts to vectorize.

        Returns
        -------
        scipy.sparse.csr_matrix
            One row per text, one column per term.

        Raises
        ------
        RuntimeError
            If the vocabulary was not learned yet.
        """
        if not self.fitted:
            raise RuntimeError("The converter must be fitted before transforming.")
        return self.vectorizer.transform(texts).tocsr()

    @staticmethod
    def _texts(x: "DashAIDataset") -> List[str]:
        """Return the first column of a dataset as strings.

        Parameters
        ----------
        x : DashAIDataset
            Dataset whose first column is text.

        Returns
        -------
        list of str
            The values, None as an empty string.
        """
        values = x.arrow_table.column(0).to_pylist()
        return ["" if value is None else str(value) for value in values]

    def fit(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "SparseTextVectorizer":
        """Learn the vocabulary of the first column.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset; only the first column is used.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        SparseTextVectorizer
            This converter.
        """
        self.fit_matrix(self._texts(x))
        return self

    def transform(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Append one column per vocabulary term to the dataset.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset; the first column is vectorized and kept.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            The input columns plus ``{COLUMN_PREFIX}{term}`` columns.

        Raises
        ------
        RuntimeError
            If :meth:`fit` was not called.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        dense = self.transform_matrix(self._texts(x)).toarray()
        arrow_type = pa.type_for_alias(self.COLUMN_DTYPE)
        output_type = self.get_output_type()
        table = x.arrow_table
        types = dict(x.types)
        for index, term in enumerate(self.vectorizer.get_feature_names_out()):
            name = f"{self.COLUMN_PREFIX}{term}"
            table = table.append_column(
                name, pa.array(dense[:, index].tolist(), type=arrow_type)
            )
            types[name] = output_type
        return DashAIDataset(table, types=types, splits=x.splits)
