from sklearn.preprocessing import MaxAbsScaler as MaxAbsScalerOperation

from DashAI.back.converters.category.scaling_and_normalization import (
    ScalingAndNormalizationConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class MaxAbsScalerSchema(BaseSchema):
    """Schema for MaxAbsScaler hyperparameters.

    ``MaxAbsScaler`` has no configurable hyperparameters in DashAI: it always
    maps each feature to [-1, 1] by dividing by the per-feature maximum
    absolute value.
    """


class MaxAbsScaler(
    ScalingAndNormalizationConverter, SklearnWrapper, MaxAbsScalerOperation
):
    """Scale each feature by its maximum absolute value to the range [-1, 1].

    For each feature column the transformation is::

        x_scaled = x / max(|x|)

    where ``max(|x|)`` is the largest absolute value observed in that column
    during fitting. The result always lies in [-1, 1].

    Because this scaler neither centers nor shifts the data, it preserves any
    existing zero entries, making it the preferred choice for sparse matrices
    (e.g. TF-IDF or count-vectorized text). It is also appropriate when the
    data is already known to be centered at zero and only the scale needs to
    be adjusted.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MaxAbsScaler.html
    """

    SCHEMA = MaxAbsScalerSchema
    DESCRIPTION = MultilingualString(
        en="Scale each feature by its maximum absolute value.",
        es="Escala cada característica por su valor absoluto máximo.",
        pt="Escala cada característica pelo seu valor absoluto máximo.",
        de="Jedes Merkmal durch seinen maximalen absoluten Wert skalieren.",
        zh="按每个特征的最大绝对值对其进行缩放。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Max Abs Scaler",
        es="Escalador Max Abs",
        pt="Escalador de Valor Absoluto Máximo",
        de="Max-Abs-Skalierer",
        zh="最大绝对值缩放器",
    )
    IMAGE_PREVIEW = "max_abs_scaler.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

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
            A Float type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
