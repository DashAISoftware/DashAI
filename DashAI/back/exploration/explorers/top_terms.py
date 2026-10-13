"""Most frequent or most distinctive terms and n-grams of text items."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.text_analysis_explorer import TextAnalysisExplorer
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

COUNT = "Count"
TFIDF = "TF-IDF"
NO_STOP_WORDS = "None"
ENGLISH = "English"
SPANISH = "Spanish"
BOTH = "English and Spanish"
SPANISH_STOP_WORDS = frozenset(
    [
        "a",
        "al",
        "algo",
        "algunas",
        "algunos",
        "ante",
        "antes",
        "como",
        "con",
        "contra",
        "cual",
        "cuales",
        "cuando",
        "de",
        "del",
        "desde",
        "donde",
        "durante",
        "e",
        "el",
        "ella",
        "ellas",
        "ellos",
        "en",
        "entre",
        "era",
        "eran",
        "es",
        "esa",
        "esas",
        "ese",
        "eso",
        "esos",
        "esta",
        "estaba",
        "estado",
        "estan",
        "estar",
        "este",
        "esto",
        "estos",
        "fue",
        "fueron",
        "ha",
        "han",
        "hasta",
        "hay",
        "la",
        "las",
        "le",
        "les",
        "lo",
        "los",
        "mas",
        "me",
        "mi",
        "mis",
        "mucho",
        "muy",
        "nada",
        "ni",
        "no",
        "nos",
        "nosotros",
        "o",
        "otra",
        "otras",
        "otro",
        "otros",
        "para",
        "pero",
        "poco",
        "por",
        "porque",
        "que",
        "quien",
        "se",
        "ser",
        "si",
        "sin",
        "sobre",
        "son",
        "su",
        "sus",
        "tambien",
        "tanto",
        "te",
        "tiene",
        "tienen",
        "todo",
        "todos",
        "tu",
        "tus",
        "un",
        "una",
        "uno",
        "unos",
        "y",
        "ya",
        "yo",
        "él",
        "más",
        "qué",
        "también",
        "está",
        "están",
        "será",
        "sí",
        "sólo",
        "solo",
        "cómo",
        "dónde",
        "cuándo",
        "este",
        "esta",
        "estas",
        "sus",
        "fue",
        "han",
        "ser",
        "sea",
        "según",
        "tras",
        "cada",
    ]
)


class TopTermsSchema(BaseExplorerSchema):
    """Schema for the top terms explorer."""

    top_n: schema_field(
        int_field(ge=1, le=200),
        20,
        description=MultilingualString(
            en="How many terms to show, between 1 and 200.",
            es="Cuántos términos mostrar, entre 1 y 200.",
            pt="Quantos termos mostrar, entre 1 e 200.",
            de="Wie viele Begriffe angezeigt werden, zwischen 1 und 200.",
            zh="显示的词条数量，介于 1 和 200 之间。",
        ),
        alias=MultilingualString(
            en="Terms shown",
            es="Términos mostrados",
            pt="Termos mostrados",
            de="Angezeigte Begriffe",
            zh="显示的词条",
        ),
    )  # type: ignore
    min_words: schema_field(
        int_field(ge=1, le=5),
        1,
        description=MultilingualString(
            en="Fewest words in a term: 1 for single words, 2 for pairs.",
            es="Mínimo de palabras por término: 1 para palabras sueltas, 2 para pares.",
            pt="Mínimo de palavras por termo: 1 para palavras soltas, 2 para pares.",
            de="Mindestzahl Wörter je Begriff: 1 für Einzelwörter, 2 für Paare.",
            zh="每个词条的最少单词数：1 表示单词，2 表示词对。",
        ),
        alias=MultilingualString(
            en="Minimum words per term",
            es="Mínimo de palabras por término",
            pt="Mínimo de palavras por termo",
            de="Mindestwörter je Begriff",
            zh="每个词条最少单词数",
        ),
    )  # type: ignore
    max_words: schema_field(
        int_field(ge=1, le=5),
        2,
        description=MultilingualString(
            en="Most words in a term; not less than the minimum.",
            es="Máximo de palabras por término; no menor que el mínimo.",
            pt="Máximo de palavras por termo; não menor que o mínimo.",
            de="Höchstzahl Wörter je Begriff; nicht kleiner als das Minimum.",
            zh="每个词条的最多单词数；不小于最少值。",
        ),
        alias=MultilingualString(
            en="Maximum words per term",
            es="Máximo de palabras por término",
            pt="Máximo de palavras por termo",
            de="Höchstwörter je Begriff",
            zh="每个词条最多单词数",
        ),
    )  # type: ignore
    score: schema_field(
        enum_field([COUNT, TFIDF]),
        COUNT,
        description=MultilingualString(
            en=(
                "Count ranks terms by how often they appear. TF-IDF favours "
                "terms that are frequent in a few items but rare elsewhere."
            ),
            es=(
                "Count ordena los términos por frecuencia. TF-IDF favorece los "
                "términos frecuentes en pocos elementos y raros en el resto."
            ),
            pt=(
                "Count ordena os termos pela frequência. TF-IDF favorece termos "
                "frequentes em poucos itens e raros nos demais."
            ),
            de=(
                "Count ordnet Begriffe nach Häufigkeit. TF-IDF bevorzugt "
                "Begriffe, die in wenigen Elementen häufig und sonst selten sind."
            ),
            zh=(
                "Count 按出现频率排序。TF-IDF 偏向在少数元素中频繁、在其他元素中少见的"
                "词条。"
            ),
        ),
        alias=MultilingualString(
            en="Ranking",
            es="Orden",
            pt="Ordenação",
            de="Rangfolge",
            zh="排序方式",
        ),
    )  # type: ignore
    stop_words: schema_field(
        enum_field([NO_STOP_WORDS, ENGLISH, SPANISH, BOTH]),
        BOTH,
        description=MultilingualString(
            en="Common words left out, such as 'the' or 'de'.",
            es="Palabras comunes que se omiten, como 'the' o 'de'.",
            pt="Palavras comuns omitidas, como 'the' ou 'de'.",
            de="Ausgelassene häufige Wörter wie 'the' oder 'de'.",
            zh="忽略的常见词，例如 'the' 或 'de'。",
        ),
        alias=MultilingualString(
            en="Stop words",
            es="Palabras vacías",
            pt="Palavras vazias",
            de="Stoppwörter",
            zh="停用词",
        ),
    )  # type: ignore
    lowercase: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="Count upper and lower case forms as the same term.",
            es="Cuenta las formas en mayúsculas y minúsculas como un mismo término.",
            pt="Conta as formas maiúsculas e minúsculas como o mesmo termo.",
            de="Groß und Kleinschreibung als denselben Begriff zählen.",
            zh="将大小写形式视为同一词条。",
        ),
        alias=MultilingualString(
            en="Ignore case",
            es="Ignorar mayúsculas",
            pt="Ignorar maiúsculas",
            de="Groß/Klein ignorieren",
            zh="忽略大小写",
        ),
    )  # type: ignore


def stop_word_list(choice: str) -> Optional[List[str]]:
    """Return the stop words for a choice of the schema.

    Parameters
    ----------
    choice : str
        One of the ``stop_words`` options.

    Returns
    -------
    Optional[List[str]]
        The words to leave out, or None to keep every word.
    """
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    words = set()
    if choice in (ENGLISH, BOTH):
        words |= ENGLISH_STOP_WORDS
    if choice in (SPANISH, BOTH):
        words |= SPANISH_STOP_WORDS
    return sorted(words) or None


class TopTermsExplorer(TextAnalysisExplorer):
    """Rank the terms and n-grams of text items by count or TF-IDF.

    Each item, or each value on a dataset, is one text. Count ranks terms by
    their total occurrences; TF-IDF ranks each term by its highest weight in
    any one item, which favours terms concentrated in a few items.
    """

    SCHEMA = TopTermsSchema
    DISPLAY_NAME = MultilingualString(
        en="Top Terms",
        es="Términos Principales",
        pt="Termos Principais",
        de="Häufigste Begriffe",
        zh="高频词条",
    )
    DESCRIPTION = MultilingualString(
        en="Bar chart of the most frequent or most distinctive words and n-grams.",
        es="Gráfico de barras de las palabras y n-gramas más frecuentes o distintivos.",
        pt="Gráfico de barras das palavras e n-gramas mais frequentes ou distintivos.",
        de="Balkendiagramm der häufigsten oder markantesten Wörter und N-Gramme.",
        zh="最常见或最具区分度的单词和 n 元组的条形图。",
    )
    metadata: Dict[str, Any] = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 1},
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(self, **kwargs) -> None:
        """Store the ranking options.

        Parameters
        ----------
        **kwargs
            ``top_n``, ``min_words``, ``max_words``, ``score``,
            ``stop_words`` and ``lowercase`` from ``TopTermsSchema``.
        """
        self.top_n = kwargs.get("top_n", 20)
        self.min_words = kwargs.get("min_words", 1)
        self.max_words = kwargs.get("max_words", 2)
        self.score = kwargs.get("score", COUNT)
        self.stop_words = kwargs.get("stop_words", BOTH)
        self.lowercase = kwargs.get("lowercase", True)
        super().__init__(**kwargs)

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> bool:
        """Validate the schema and that the term length range is ordered.

        Parameters
        ----------
        params : Dict[str, Any]
            The explorer parameters.

        Returns
        -------
        bool
            False when the minimum words per term exceed the maximum.

        Raises
        ------
        ValidationError
            If the parameters do not match the schema.
        """
        parsed = cls.SCHEMA.model_validate(params)
        return parsed.min_words <= parsed.max_words

    def rank(self, values: List[str]) -> List[tuple]:
        """Return the top terms of the texts with their scores.

        Parameters
        ----------
        values : List[str]
            The texts.

        Returns
        -------
        List[tuple]
            ``(term, score)`` pairs, best first; empty when no term is left.
        """
        from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

        vectorizer_class = TfidfVectorizer if self.score == TFIDF else CountVectorizer
        vectorizer = vectorizer_class(
            ngram_range=(self.min_words, self.max_words),
            stop_words=stop_word_list(self.stop_words),
            lowercase=self.lowercase,
            token_pattern=r"(?u)\b[^\W\d_]{2,}\b",
        )
        texts = [value for value in values if value.strip()]
        if not texts:
            return []
        try:
            matrix = vectorizer.fit_transform(texts)
        except ValueError:
            return []
        scores = (
            matrix.max(axis=0).toarray().ravel()
            if self.score == TFIDF
            else matrix.sum(axis=0).A1
        )
        terms = vectorizer.get_feature_names_out()
        order = sorted(range(len(terms)), key=lambda i: (-scores[i], terms[i]))
        return [(terms[i], float(scores[i])) for i in order[: self.top_n]]

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Build a horizontal bar chart of the top terms.

        Parameters
        ----------
        dataset : DashAIDataset
            The selected text.
        explorer_info : Explorer
            The explorer record.

        Returns
        -------
        plotly.graph_objects.Figure
            The top terms, best at the top.
        """
        import plotly.graph_objects as go

        ranked = self.rank(self.text_column(dataset, explorer_info))
        terms = [term for term, _ in reversed(ranked)]
        scores = [round(score, 4) for _, score in reversed(ranked)]
        figure = go.Figure(go.Bar(x=scores, y=terms, orientation="h"))
        figure.update_layout(
            title=explorer_info.name or f"Top terms ({self.score})",
            xaxis_title=self.score,
            height=max(400, 24 * len(terms) + 160),
        )
        if not ranked:
            figure.add_annotation(
                text="No terms left after removing stop words.",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
            )
        return figure
