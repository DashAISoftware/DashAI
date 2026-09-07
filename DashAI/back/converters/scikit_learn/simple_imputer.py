from typing import TYPE_CHECKING, Union

from sklearn.impute import SimpleImputer as SimpleImputerOperation

from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
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
