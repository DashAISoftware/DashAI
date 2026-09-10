from sklearn.preprocessing import StandardScaler as StandardScalerOperation

from DashAI.back.converters.category.scaling_and_normalization import (
    ScalingAndNormalizationConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class StandardScalerSchema(BaseSchema):
    """Schema for StandardScaler hyperparameters.

    Configures the mean centering, variance scaling, and copy semantics for
    sklearn's ``StandardScaler``. The ``with_mean`` and ``with_std`` flags
    allow independent control over whether the mean is subtracted and whether
    the result is divided by the standard deviation.
    """

    with_mean: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="If True, center the data before scaling.",
            es="Si es True, centra los datos antes de escalar.",
            pt="Se True, centraliza os dados antes de escalonar.",
            de="Wenn True, werden die Daten vor der Skalierung zentriert.",
            zh="如果为 True，则在缩放前对数据进行中心化。",
        ),
    )  # type: ignore
    with_std: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "If True, scale the data to unit variance (or equivalently, "
                "unit standard deviation)."
            ),
            es=(
                "Si es True, escala los datos a varianza unitaria (o "
                "equivalentemente, desviación estándar unitaria)."
            ),
            pt=(
                "Se True, escala os dados para variância unitária (ou "
                "equivalentemente, desvio padrão unitário)."
            ),
            de=(
                "Wenn True, werden die Daten auf Einheitsvarianz skaliert (oder "
                "äquivalent, Einheitsstandardabweichung)."
            ),
            zh="如果为 True，则将数据缩放到单位方差（或等价地，单位标准差）。",
        ),
    )  # type: ignore


class StandardScaler(
    ScalingAndNormalizationConverter, SklearnWrapper, StandardScalerOperation
):
    """Standardize features by removing the mean and scaling to unit variance.

    For each feature column the transformation (z-score normalization) is::

        x_scaled = (x - mean) / std

    where ``mean`` and ``std`` are estimated from the training data. The
    result has zero mean and unit standard deviation. Centering and scaling
    can be disabled independently via ``with_mean`` and ``with_std``.

    Standardization is the most common preprocessing step for algorithms that
    assume normally distributed or zero-mean inputs, including SVMs, logistic
    regression, linear regression with regularization, principal component
    analysis, and most neural networks. Unlike ``MinMaxScaler``, it is robust
    to differences in feature range but not to extreme outliers (because the
    standard deviation is influenced by them).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
    """

    SCHEMA = StandardScalerSchema
    DESCRIPTION = MultilingualString(
        en=("Standardize features by removing the mean and scaling to unit variance."),
        es=(
            "Estandariza las características eliminando la media y escalando "
            "a varianza unitaria."
        ),
        pt=(
            "Padroniza as características removendo a média e escalonando "
            "para variância unitária."
        ),
        de=(
            "Merkmale standardisieren, indem der Mittelwert entfernt und auf "
            "Einheitsvarianz skaliert wird."
        ),
        zh="通过去除均值并缩放到单位方差来标准化特征。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Standard Scaler",
        es="Estandarizador",
        pt="Normalizador Padrão",
        de="Standardisierer",
        zh="标准化缩放器",
    )

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

    IMAGE_PREVIEW = "standard_scaler.png"
