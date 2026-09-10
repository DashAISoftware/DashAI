from sklearn.preprocessing import OrdinalEncoder as OrdinalEncoderOperation

from DashAI.back.api.utils import cast_string_to_type
from DashAI.back.converters.category.encoding import EncodingConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
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
from DashAI.back.types.value_types import Integer


class OrdinalEncoderSchema(BaseSchema):
    """Schema for OrdinalEncoder hyperparameters.

    Configures the category ordering, output dtype, unknown-value handling,
    and infrequent-category grouping for sklearn's ``OrdinalEncoder``. The
    ``handle_unknown`` field determines whether an unseen category at
    transform time raises an error or is replaced by a sentinel value
    specified in ``unknown_value``.
    """

    categories: schema_field(
        string_field(),
        "auto",
        description=MultilingualString(
            en="Categories (unique values) per feature.",
            es="Categorías (valores únicos) por característica.",
            pt="Categorias (valores únicos) por característica.",
            de="Kategorien (eindeutige Werte) pro Merkmal.",
            zh="每个特征的类别（唯一值）。",
        ),
    )  # type: ignore
    dtype: schema_field(
        enum_field(["int32", "int64"]),
        "int64",
        description=MultilingualString(
            en="Desired dtype of output.",
            es="Tipo de dato de salida deseado.",
            pt="Tipo de dado de saída desejado.",
            de="Gewünschter Datentyp der Ausgabe.",
            zh="所需的输出数据类型。",
        ),
    )  # type: ignore
    handle_unknown: schema_field(
        enum_field(["error", "use_encoded_value"]),
        "error",
        description=MultilingualString(
            en=(
                "Whether to raise an error or use a specific encoded value when "
                "an unknown category is seen."
            ),
            es=(
                "Si se debe lanzar un error o usar un valor codificado específico "
                "cuando se vea una categoría desconocida."
            ),
            pt=(
                "Se deve lançar um erro ou usar um valor codificado específico "
                "quando uma categoria desconhecida for encontrada."
            ),
            de=(
                "Ob ein Fehler ausgelöst oder ein spezifischer kodierter Wert verwendet"
                "werden soll, "
                "wenn eine unbekannte Kategorie gesehen wird."
            ),
            zh="遇到未知类别时是报错还是使用特定的编码值。",
        ),
    )  # type: ignore
    unknown_value: schema_field(
        # sklearn wants an actual number here, or nan. The old enum offered the
        # type names "int" and "np.nan" as if they were values: "np.nan" was
        # translated by cast_string_to_type, but "int" reached sklearn as the
        # class `int` and was rejected. A user needs to type the sentinel
        # integer, so the int branch is a real number field now.
        none_type(union_type(int_field(), enum_field(["np.nan"]))),
        None,
        description=MultilingualString(
            en="The value to use for unknown categories.",
            es="El valor a usar para categorías desconocidas.",
            pt="O valor a usar para categorias desconhecidas.",
            de="Der Wert für unbekannte Kategorien.",
            zh="用于未知类别的值。",
        ),
    )  # type: ignore
    # Added in version 1.3
    min_frequency: schema_field(
        none_type(union_type(int_field(ge=1), float_field(ge=0.0, le=1.0))),
        None,
        description=MultilingualString(
            en="Minimum frequency of a category to be considered as frequent.",
            es="Frecuencia mínima para considerar una categoría como frecuente.",
            pt="Frequência mínima para considerar uma categoria como frequente.",
            de="Mindesthäufigkeit einer Kategorie, um als häufig betrachtet zu werden.",
            zh="将类别视为频繁类别的最低频率。",
        ),
    )  # type: ignore
    # Added in version 1.3
    max_categories: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en="Maximum number of categories to encode.",
            es="Número máximo de categorías a codificar.",
            pt="Número máximo de categorias a codificar.",
            de="Maximale Anzahl der zu kodierenden Kategorien.",
            zh="要编码的最大类别数。",
        ),
    )  # type: ignore


class OrdinalEncoder(EncodingConverter, SklearnWrapper, OrdinalEncoderOperation):
    """Encode categorical feature columns as integer ordinal codes.

    For each input feature column every unique category value is mapped to a
    contiguous integer starting at 0. Given categories ``["cold", "warm",
    "hot"]`` sorted alphabetically the default mapping would be
    ``cold -> 0``, ``hot -> 1``, ``warm -> 2``; a custom category list can
    be supplied to impose a domain-specific order.

    Unlike ``OneHotEncoder``, ordinal encoding produces a single output
    column per input column and implicitly encodes a numerical order between
    the categories. This makes it appropriate when:

    * The categories have a meaningful rank (e.g. education level, severity
      score, shirt size).
    * The downstream model can exploit ordinal structure (e.g. tree based
      models such as gradient-boosted trees or random forests).

    For unordered nominal categories, ``OneHotEncoder`` is typically
    preferred because ordinal codes introduce a spurious ordering.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OrdinalEncoder.html
    """

    SCHEMA = OrdinalEncoderSchema
    DESCRIPTION = MultilingualString(
        en="Encode categorical features as an integer array.",
        es="Codifica características categóricas como un arreglo de enteros.",
        pt="Codifica características categóricas como um array de inteiros.",
        de="Kategoriale Merkmale als Ganzzahl-Array kodieren.",
        zh="将类别特征编码为整数数组。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Ordinal Encoder",
        es="Codificador Ordinal",
        pt="Codificador Ordinal",
        de="Ordinaler Kodierer",
        zh="序数编码器",
    )
    IMAGE_PREVIEW = "ordinal_encoder.png"

    PREFIX = "oe_"

    metadata = {
        "allowed_types": [Categorical],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the OrdinalEncoder converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. ``dtype``, ``unknown_value``, and
            ``min_frequency`` string values are cast to their corresponding
            NumPy or Python types before being forwarded to the underlying
            scikit-learn class.
        """
        self.dtype = kwargs.pop("dtype", "np.float64")
        self.dtype = cast_string_to_type(self.dtype)
        kwargs["dtype"] = self.dtype

        self.unknown_value = kwargs.pop("unknown_value", None)
        if self.unknown_value is not None:
            self.unknown_value = cast_string_to_type(self.unknown_value)
        kwargs["unknown_value"] = self.unknown_value

        self.min_frequency = kwargs.pop("min_frequency", None)
        if self.min_frequency is not None:
            self.min_frequency = cast_string_to_type(self.min_frequency)
        kwargs["min_frequency"] = self.min_frequency

        super().__init__(**kwargs)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            Not used; all output columns share the
            same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            A placeholder ``Integer`` type with the same dtype
            as the encoder's output. The actual categories will
            be set by sklearn_wrapper's transform method.

        """
        import pyarrow as pa

        # Return a placeholder categorical type
        # The actual categories will be set by sklearn_wrapper's transform method
        return Integer(arrow_type=pa.from_numpy_dtype(self.dtype))
