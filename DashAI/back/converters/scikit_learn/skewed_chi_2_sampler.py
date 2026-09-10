from sklearn.kernel_approximation import SkewedChi2Sampler as SkewedChi2SamplerOperation

from DashAI.back.api.utils import create_random_state
from DashAI.back.converters.category.polynomial_kernel import PolynomialKernelConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class SkewedChi2SamplerSchema(BaseSchema):
    """Schema for configuring the SkewedChi2Sampler converter.

    Wraps ``sklearn.kernel_approximation.SkewedChi2Sampler`` and exposes the
    kernel skewedness parameter, the number of random Fourier components, and
    the random seed as schema fields validated before being forwarded to the
    underlying scikit-learn estimator.
    """

    skewedness: schema_field(
        float_field(gt=0),
        1.0,
        description=MultilingualString(
            en="The skewedness parameter of the chi-squared kernel.",
            es="El parámetro de sesgo del kernel chi-cuadrado.",
            pt="O parâmetro de enviesamento do kernel qui-quadrado.",
            de="Der Schiefheitsparameter des Chi-Quadrat-Kernels.",
            zh="卡方核的偏斜参数。",
        ),
    )  # type: ignore
    n_components: schema_field(
        int_field(ge=1),
        100,
        description=MultilingualString(
            en=(
                "Number of Monte Carlo samples per original feature. Equals the "
                "dimensionality of the computed feature space."
            ),
            es=(
                "Número de muestras de Monte Carlo por característica original. "
                "Equivale a la dimensionalidad del espacio de características "
                "calculado."
            ),
            pt=(
                "Número de amostras de Monte Carlo por característica original. "
                "Equivale à dimensionalidade do espaço de características calculado."
            ),
            de=(
                "Anzahl der Monte-Carlo-Stichproben pro ursprünglichem Merkmal. "
                "Entspricht der Dimensionalität des berechneten Merkmalsraums."
            ),
            zh="每个原始特征的蒙特卡罗样本数，等于计算出的特征空间的维度。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(union_type(int_field(), enum_field(["RandomState"]))),
        None,
        description=MultilingualString(
            en=(
                "Pseudo-random number generator to control the generation of the "
                "random weights and random offset when fitting the training data. "
                "Pass an int for reproducible output across multiple function calls."
            ),
            es=(
                "Generador pseudoaleatorio para controlar la generación de pesos y "
                "desplazamientos aleatorios al ajustar los datos. Pasa un entero "
                "para obtener resultados reproducibles."
            ),
            pt=(
                "Gerador pseudoaleatório para controlar a geração de pesos e "
                "deslocamentos aleatórios ao ajustar os dados. Passe um inteiro "
                "para obter resultados reproduzíveis."
            ),
            de=(
                "Pseudozufallszahlengenerator zur Steuerung der Erzeugung zufälliger "
                "Gewichte und Versätze beim Anpassen der Trainingsdaten. "
                "Ganzzahl übergeben für reproduzierbare Ausgabe."
            ),
            zh=(
                "用于控制拟合训练数据时随机权重和随机偏移生成的伪随机数生成器。"
                "传入整数以获得可重现的输出。"
            ),
        ),
    )  # type: ignore


class SkewedChi2Sampler(
    PolynomialKernelConverter, SklearnWrapper, SkewedChi2SamplerOperation
):
    """Approximate the skewed chi-squared kernel feature map
    via random Fourier features.

    The skewed chi-squared kernel is well suited for histogram-based features
    (e.g. visual bag-of-words, colour histograms) and is defined as:

        K(x, y) = prod_j  2 * sqrt(x_j + c) * sqrt(y_j + c) /
                            (x_j + y_j + 2c)

    where *c* is the ``skewedness`` parameter. A ``skewedness`` value of 0
    recovers the ordinary chi-squared kernel; larger values reduce the
    sensitivity to small feature values.

    This converter maps inputs to a ``n_components``-dimensional random Fourier
    feature space in which a dot product approximates the above kernel,
    following the approach of Rahimi & Recht (2007) [2]. Training a linear
    classifier on the resulting features approximates an SVM with the skewed
    chi-squared kernel.

    Output columns are typed as ``Float64`` in DashAI.

    Wraps ``sklearn.kernel_approximation.SkewedChi2Sampler``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.kernel_approximation.SkewedChi2Sampler.html
    - [2] Rahimi, A. & Recht, B. (2007). Random Features for Large-Scale Kernel
        Machines. Advances in Neural Information Processing Systems, 20.
    """

    SCHEMA = SkewedChi2SamplerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Approximates the feature map of a chi-squared kernel by Monte Carlo "
            "approximation of its Fourier transform."
        ),
        es=(
            "Aproxima el mapa de características de un kernel chi-cuadrado "
            "mediante la aproximación de Monte Carlo de su transformada de Fourier."
        ),
        pt=(
            "Aproxima o mapa de características de um kernel qui-quadrado por "
            "aproximação de Monte Carlo de sua transformada de Fourier."
        ),
        de=(
            "Approximiert die Merkmalszuordnung eines Chi-Quadrat-Kernels durch "
            "Monte-Carlo-Approximation seiner Fourier-Transformation."
        ),
        zh="通过蒙特卡罗近似其傅里叶变换来近似卡方核的特征映射。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Skewed Chi² Sampler",
        es="Muestreador Chi² Sesgado",
        pt="Amostrador Qui-2 Enviesado",
        de="Schiefer Chi²-Stichprobennehmer",
        zh="偏斜卡方采样器",
    )
    IMAGE_PREVIEW = "skewed_chi2_sampler.png"

    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialise the skewed chi-squared sampler,
        resolving the ``"RandomState"`` sentinel.

        If ``random_state`` is the string ``"RandomState"``, a fresh
        ``numpy.random.RandomState`` instance is created in its place before
        being forwarded to sklearn's ``SkewedChi2Sampler``.

        Parameters
        ----------
        **kwargs : dict
            random_state : int, ``"RandomState"``, or None, optional
                Seed for reproducibility.  The special string ``"RandomState"``
                generates a fresh random state. Default ``None``.
            Additional keys are forwarded to
            ``sklearn.kernel_approximation.SkewedChi2Sampler``.
        """
        self.random_state = kwargs.pop("random_state", None)
        if self.random_state == "RandomState":
            self.random_state = create_random_state()
        kwargs["random_state"] = self.random_state

        super().__init__(**kwargs)

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
