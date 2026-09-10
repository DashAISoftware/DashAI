from sklearn.kernel_approximation import (
    AdditiveChi2Sampler as AdditiveChi2SamplerOperation,
)

from DashAI.back.converters.category.polynomial_kernel import PolynomialKernelConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    float_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class AdditiveChi2SamplerSchema(BaseSchema):
    """Schema for AdditiveChi2Sampler hyperparameters."""

    sample_steps: schema_field(
        int_field(ge=1),
        2,
        description=MultilingualString(
            en="The number of sample steps (shuffling) to perform.",
            es="Número de pasos de muestreo (mezcla) a realizar.",
            pt="O número de passos de amostragem (embaralhamento) a realizar.",
            de="Die Anzahl der Stichprobenschritte (Mischen) zur Durchführung.",
            zh="要执行的采样步骤（混洗）数量。",
        ),
    )  # type: ignore
    sample_interval: schema_field(
        none_type(float_field(ge=1.0)),
        None,
        description=MultilingualString(
            en="The number of samples generated between each original sample.",
            es="Número de muestras generadas entre cada muestra original.",
            pt="O número de amostras geradas entre cada amostra original.",
            de=(
                "Die Anzahl der zwischen jeder ursprünglichen Stichprobe generierten "
                "Stichproben."
            ),
            zh="每个原始样本之间生成的样本数量。",
        ),
    )  # type: ignore


class AdditiveChi2Sampler(
    PolynomialKernelConverter, SklearnWrapper, AdditiveChi2SamplerOperation
):
    """Approximate the additive chi-squared kernel using Fourier sampling.

    Maps features to a higher-dimensional space that approximates the additive
    chi-squared kernel, enabling efficient linear classification. Wraps
    scikit-learn's ``AdditiveChi2Sampler``.
    """

    SCHEMA = AdditiveChi2SamplerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Uses sampling the Fourier transform of the kernel characteristic "
            "at regular intervals."
        ),
        es=(
            "Utiliza muestreo de la transformada de Fourier de la función kernel "
            "a intervalos regulares."
        ),
        pt=(
            "Utiliza amostragem da transformada de Fourier da característica do "
            "kernel em intervalos regulares."
        ),
        de=(
            "Verwendet Stichproben der Fourier-Transformation der Kerneleigenschaft "
            "in regelmäßigen Abständen."
        ),
        zh="以规则间隔对核特征的傅里叶变换进行采样。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Additive Chi² Sampler",
        es="Muestreador Chi² Aditivo",
        pt="Amostrador Qui-2 Aditivo",
        de="Additiver Chi²-Stichprobennehmer",
        zh="加性卡方采样器",
    )
    IMAGE_PREVIEW = "additive_chi2_sampler.png"

    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            Not used; all output columns share the same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Float type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
