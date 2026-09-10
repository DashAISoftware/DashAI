from typing import TYPE_CHECKING, Union

from sklearn.impute import SimpleImputer as SimpleImputerOperation

from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    Check,
    Eq,
    F,
    IsNull,
    Not,
    Relevance,
    bool_field,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    string_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SimpleImputerSchema(BaseSchema):
    """Schema for configuring the SimpleImputer converter.

    Wraps ``sklearn.impute.SimpleImputer`` and exposes strategy selection,
    fill value, copy behaviour, indicator stacking, and empty-feature
    handling as schema fields validated before being forwarded to the
    underlying scikit-learn estimator.
    """

    strategy: schema_field(
        enum_field(
            [
                "mean",
                "median",
                "most_frequent",
                "constant",
            ]
        ),
        "mean",
        description=MultilingualString(
            en="The imputation strategy.",
            es="La estrategia de imputación.",
            pt="A estratégia de imputação.",
            de="Die Imputationsstrategie.",
            zh="插补策略。",
        ),
    )  # type: ignore
    fill_value: schema_field(
        none_type(union_type(int_field(), union_type(float_field(), string_field()))),
        None,
        description=MultilingualString(
            en="The value to replace missing values with.",
            es="El valor para reemplazar los valores faltantes.",
            pt="O valor para substituir os valores ausentes.",
            de="Der Wert zum Ersetzen fehlender Werte.",
            zh="用于替换缺失值的填充值。",
        ),
    )  # type: ignore
    add_indicator: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="If True, a MissingIndicator transform will stack onto output.",
            es=("Si es True, se apilará un MissingIndicator sobre la salida."),
            pt=("Se True, uma transformação MissingIndicator será empilhada na saída."),
            de=(
                "Wenn True, wird eine MissingIndicator-Transformation auf die Ausgabe "
                "gestapelt."
            ),
            zh="如果为 True，则将 MissingIndicator 变换叠加到输出上。",
        ),
    )  # type: ignore
    keep_empty_features: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="If True, empty features will be kept.",
            es="Si es True, se mantendrán las características vacías.",
            pt="Se True, características vazias serão mantidas.",
            de="Wenn True, werden leere Merkmale beibehalten.",
            zh="如果为 True，则保留空特征。",
        ),
    )  # type: ignore

    # scikit-learn reads `fill_value` only when the strategy is "constant" and
    # silently ignores it otherwise: with strategy="mean" and fill_value=99 it
    # imputes the mean and never says a word, so a value the user typed and
    # dashAI persisted is quietly discarded. And with strategy="constant" and
    # no fill value, sklearn substitutes 0 (or "missing_value" for object
    # columns) rather than asking. Both are stated here instead of nowhere,
    # which is where the dependency lived before: unlike the holdout seed, it
    # was not even mentioned in the field's description.
    #
    # The Check needs no strategy condition of its own: a check whose target a
    # relevance rule has marked irrelevant does not run, so this one applies
    # exactly when `fill_value` is meaningful.
    rules = [
        Relevance(
            "fill_value",
            when=Eq(F("strategy"), "constant"),
            effect="disable",
            reason=MultilingualString(
                en=(
                    'The fill value is only used by the "constant" strategy; '
                    "the others compute the replacement from the data."
                ),
                es=(
                    'El valor de relleno solo lo usa la estrategia "constant"; '
                    "las demás calculan el reemplazo a partir de los datos."
                ),
                pt=(
                    'O valor de preenchimento só é usado pela estratégia "constant"; '
                    "as outras calculam a substituição a partir dos dados."
                ),
                de=(
                    'Der Füllwert wird nur von der Strategie "constant" verwendet; '
                    "die anderen berechnen den Ersatzwert aus den Daten."
                ),
                zh="填充值仅用于 constant 策略；其他策略从数据中计算替换值。",
            ),
        ),
        Check(
            Not(IsNull(F("fill_value"))),
            id="simple_imputer.constant_needs_fill_value",
            targets=["fill_value"],
            message=MultilingualString(
                en=(
                    'The "constant" strategy needs a fill value. Left empty, '
                    "missing values become 0 for numeric columns."
                ),
                es=(
                    'La estrategia "constant" necesita un valor de relleno. Si se '
                    "deja vacío, los valores faltantes quedan en 0 en las columnas "
                    "numéricas."
                ),
                pt=(
                    'A estratégia "constant" precisa de um valor de preenchimento. '
                    "Se ficar vazio, os valores ausentes tornam-se 0 nas colunas "
                    "numéricas."
                ),
                de=(
                    'Die Strategie "constant" benötigt einen Füllwert. Bleibt er '
                    "leer, werden fehlende Werte in numerischen Spalten zu 0."
                ),
                zh="constant 策略需要填充值。留空时，数值列的缺失值将变为 0。",
            ),
        ),
    ]


class SimpleImputer(
    BasicPreprocessingConverter, SklearnWrapper, SimpleImputerOperation
):
    """Fill missing values using a simple univariate per-column strategy.

    Each feature is imputed independently using one of four strategies:

    * ``"mean"``: replace missing values with the column mean (numeric only).
    * ``"median"``: replace with the column median (numeric only).
    * ``"most_frequent"``: replace with the most common value (works with
      strings and numeric data).
    * ``"constant"``: replace with a fixed ``fill_value`` supplied by the
      user.

    Columns with all-missing values are handled according to the
    ``keep_empty_features`` flag. When ``add_indicator=True``, a
    ``MissingIndicator`` binary matrix is stacked onto the output.

    Output typing preserves the original column type whenever the strategy
    does not force a fractional result: ``"most_frequent"`` and
    ``"constant"`` never perform arithmetic, so the source type (Integer,
    Float, or Categorical) is kept. For ``"mean"``/``"median"`` the computed
    per-column statistic is inspected, and an originally-Integer column
    stays ``Integer`` if that statistic happens to be a whole number (e.g. a
    median over an odd count of integers); otherwise it becomes ``Float64``.

    Wraps ``sklearn.impute.SimpleImputer``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html
    """

    SCHEMA = SimpleImputerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Univariate imputer for completing missing values with simple "
            "strategies. Replace missing values using a descriptive statistic "
            "(e.g. mean, median, or most frequent) along each column, or using "
            "a constant value."
        ),
        es=(
            "Imputador univariante para completar valores faltantes con "
            "estrategias simples. Reemplaza valores faltantes usando una "
            "estadística descriptiva (p. ej., media, mediana o más frecuente) "
            "por columna, o usando un valor constante."
        ),
        pt=(
            "Imputador univariado para completar valores ausentes com "
            "estratégias simples. Substitui valores ausentes usando uma "
            "estatística descritiva (p. ex., média, mediana ou moda) "
            "por coluna, ou usando um valor constante."
        ),
        de=(
            "Univariater Imputierer zum Vervollständigen fehlender Werte mit einfachen "
            "Strategien. Fehlende Werte werden durch eine deskriptive Statistik "
            "(z.B. Mittelwert, Median oder häufigster Wert) entlang jeder Spalte "
            "oder durch einen konstanten Wert ersetzt."
        ),
        zh=(
            "用于通过简单策略完成缺失值插补的单变量插补器。"
            "使用每列的描述性统计量（如均值、中位数或众数）或常数值替换缺失值。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Simple Imputer",
        es="Imputador Simple",
        pt="Imputador Simples",
        de="Einfacher Imputierer",
        zh="简单插补器",
    )
    IMAGE_PREVIEW = "simple_imputer.png"

    metadata = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the SimpleImputer converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        super().__init__(**kwargs)

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "SimpleImputer":
        """Fit the imputer, remembering input types and column order.

        These are needed by ``get_output_type`` to preserve the original
        column type instead of always coercing to ``Float64``.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to fit the imputer on.
        y : DashAIDataset, optional
            Ignored; present for API consistency.

        Returns
        -------
        SimpleImputer
            The fitted imputer instance (self).
        """
        if hasattr(x, "types") and x.types is not None:
            self._input_types = dict(x.types)
        self._input_columns = {name: idx for idx, name in enumerate(x.column_names)}
        return super().fit(x, y)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            The name of the output column. Defaults to None.

        Returns
        -------
        DashAIDataType
            ``Integer`` for the binary ``MissingIndicator`` columns appended
            when ``add_indicator=True``. Otherwise, the original column type
            for ``"most_frequent"``/``"constant"`` (no arithmetic is performed
            on the values), or for ``"mean"``/``"median"``, ``Integer`` if the
            source column was an Integer and the computed statistic is a
            whole number — otherwise a Float type backed by
            ``pyarrow.float64()``.
        """
        import pyarrow as pa

        if column_name and str(column_name).startswith("missingindicator_"):
            return Integer(arrow_type=pa.int64())

        input_types = getattr(self, "_input_types", None)
        input_type = input_types.get(column_name) if input_types else None

        if self.strategy in ("most_frequent", "constant"):
            if input_type is not None:
                return input_type
            return Float(arrow_type=pa.float64())

        if isinstance(input_type, Integer):
            columns = getattr(self, "_input_columns", None)
            statistics = getattr(self, "statistics_", None)
            if (
                columns is not None
                and statistics is not None
                and column_name in columns
            ):
                value = statistics[columns[column_name]]
                if float(value).is_integer():
                    return Integer(arrow_type=pa.int64())

        return Float(arrow_type=pa.float64())
