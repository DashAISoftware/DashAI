from typing import TYPE_CHECKING, Union

from DashAI.back.converters.category.encoding import EncodingConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class LabelEncoderSchema(BaseSchema):
    """Schema for LabelEncoder hyperparameters.

    Placeholder schema for sklearn's ``LabelEncoder``. The encoder has no
    user-configurable hyperparameters; the schema is kept for consistency with
    the DashAI component registration pattern.
    """


class LabelEncoder(EncodingConverter, SklearnWrapper):
    """Encode categorical labels as contiguous integer codes in [0, n_classes - 1].

    Each unique label value is mapped to a unique integer in ascending order
    of the sorted class list. For example, given classes ``["cat", "dog",
    "fish"]`` the mapping is ``cat -> 0``, ``dog -> 1``, ``fish -> 2``.

    Unlike ``OrdinalEncoder`` (which operates on feature columns),
    ``LabelEncoder`` is designed for target label columns. It is typically
    applied to the output column before training classifiers that require
    numeric class indices (e.g. gradient-boosted trees, support vector
    machines, or any model that indexes a class-weight array). The DashAI
    implementation extends the sklearn behaviour to support multiple columns
    and to preserve ``NaN`` values during transformation.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.LabelEncoder.html
    """

    SCHEMA = LabelEncoderSchema
    DESCRIPTION = MultilingualString(
        en="Encode target labels with value between 0 and n_classes-1.",
        es="Codifica etiquetas objetivo con valores entre 0 y n_clases-1.",
        pt="Codifica rótulos alvo com valores entre 0 e n_classes-1.",
        de="Zielgrößen mit Werten zwischen 0 und n_Klassen-1 kodieren.",
        zh="将目标标签编码为 0 到 n_classes-1 之间的值。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Convert categorical labels to numeric values",
        es="Convierte etiquetas categóricas a valores numéricos",
        pt="Converte rótulos categóricos em valores numéricos",
        de="Kategoriale Zielgrößen in numerische Werte umwandeln",
        zh="将类别标签转换为数值",
    )
    DISPLAY_NAME = MultilingualString(
        en="Label Encoder",
        es="Codificador de Etiquetas",
        pt="Codificador de Rótulos",
        de="Zielgrößen-Kodierer",
        zh="标签编码器",
    )
    IMAGE_PREVIEW = "label_encoder.png"

    PREFIX = "le_"

    metadata = {
        "changes_data_types": True,
        "allowed_types": [Categorical],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the LabelEncoder converter.

        Initializes the per-column encoder registry (``self.encoders``) and the
        list of fitted columns (``self.fitted_columns``). Note that ``kwargs``
        are not forwarded to the underlying scikit-learn class.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Not forwarded to the parent class.
        """
        super().__init__()
        self.encoders = {}
        self.fitted_columns = []

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            Not used. Defaults to None.

        Returns
        -------
        DashAIDataType
            An Integer type backed by ``pyarrow.int64()``, representing the
            contiguous integer label codes produced by the encoder.
        """
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())

    def fit(self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None):
        """Fit a LabelEncoder for each eligible column in the dataset.

        Only columns with string, object, or category dtype (or a matching
        DashAI type) are processed. NaN values are masked out before fitting.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset whose categorical/string columns will be encoded.
        y : DashAIDataset or None, optional
            Ignored. Present for API compatibility. Default ``None``.

        Returns
        -------
        LabelEncoderConverter
            The fitted converter instance (``self``).
        """
        from sklearn.preprocessing import LabelEncoder as LabelEncoderOperation

        x_pandas = x.to_pandas()

        for col in x_pandas.columns:
            # Check if column type is in allowed_dtypes using DashAI types
            col_type = x.types.get(col)
            col_dtype = col_type.dtype if hasattr(col_type, "dtype") else None

            # Allow string dtype or if it's a string-like pandas dtype
            is_allowed = col_dtype in self.metadata["allowed_dtypes"] or x_pandas[
                col
            ].dtype.name in ["object", "category", "string"]

            if is_allowed:
                mask = x_pandas[col].notna()
                if mask.any():
                    encoder = LabelEncoderOperation()
                    encoder.fit(x_pandas.loc[mask, col])
                    self.encoders[col] = encoder
                    self.fitted_columns.append(col)

        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Apply fitted label encoders and append encoded columns with a prefix.

        Encodes each fitted column and appends the result as a new
        ``encoded_<col>`` column. The original column is left unchanged.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset. Columns not seen during ``fit`` are left unchanged.
        y : DashAIDataset or None, optional
            Ignored. Present for API compatibility. Default ``None``.

        Returns
        -------
        DashAIDataset
            Dataset with original columns preserved plus new ``encoded_*``
            columns appended containing the integer label codes.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        x_pandas = x.to_pandas()

        combined_table = x.arrow_table
        combined_types = dict(x.types)

        for col in self.fitted_columns:
            if col not in x_pandas.columns:
                continue
            series = x_pandas[col].copy()
            mask = series.notna()
            if mask.any():
                series.loc[mask] = self.encoders[col].transform(series.loc[mask])
            prefixed = f"{self.PREFIX}{col}"
            combined_table = combined_table.append_column(
                prefixed, pa.array(series.tolist(), type=pa.int64())
            )
            combined_types[prefixed] = self.get_output_type(col)

        return DashAIDataset(combined_table, types=combined_types, splits=x.splits)
