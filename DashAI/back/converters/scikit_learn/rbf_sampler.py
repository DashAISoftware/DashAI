from sklearn.kernel_approximation import RBFSampler as RBFSamplerOperation

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


class RBFSamplerSchema(BaseSchema):
    """Schema for configuring the RBFSampler converter.

    Wraps ``sklearn.kernel_approximation.RBFSampler`` and exposes the RBF
    bandwidth parameter ``gamma``, the number of random Fourier features
    ``n_components``, and the random seed as schema fields validated before
    being forwarded to the underlying scikit-learn estimator.
    """

    gamma: schema_field(
        union_type(enum_field(["scale"]), float_field(gt=0)),
        "scale",
        description=MultilingualString(
            en="Parameter of the RBF kernel.",
            es="Parámetro del kernel RBF.",
            pt="Parâmetro do kernel RBF.",
            de="Parameter des RBF-Kernels.",
            zh="RBF 核的参数。",
        ),
    )  # type: ignore
    n_components: schema_field(
        int_field(ge=1),
        100,
        description=MultilingualString(
            en="The number of features to construct.",
            es="El número de características a construir.",
            pt="O número de características a construir.",
            de="Die Anzahl der zu konstruierenden Merkmale.",
            zh="要构建的特征数量。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(union_type(int_field(), enum_field(["RandomState"]))),
        0,
        description=MultilingualString(
            en=(
                "Pseudo-random number generator to control the generation of the "
                "random weights and random offset when fitting the training data. "
                "Pass an int for reproducible output across multiple function calls."
            ),
            es=(
                "Generador pseudoaleatorio para controlar pesos y desplazamientos "
                "aleatorios al ajustar los datos. Pasa un entero para obtener "
                "resultados reproducibles."
            ),
            pt=(
                "Gerador pseudoaleatório para controlar pesos e deslocamentos "
                "aleatórios ao ajustar os dados. Passe um inteiro para obter "
                "resultados reproduzíveis."
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


class RBFSampler(PolynomialKernelConverter, SklearnWrapper, RBFSamplerOperation):
    """Approximate the RBF (Gaussian) kernel feature map via random Fourier features.

    The Radial Basis Function (RBF) kernel is one of the most widely used
    kernels in kernel-based learning methods such as SVMs. Computing it
    directly scales quadratically with the number of training samples.

    This converter implements the random Fourier feature approximation of
    Rahimi & Recht (2007) [2]: random weights are sampled from the Fourier
    transform of the RBF kernel (a Gaussian distribution), and the input
    features are mapped to ``n_components`` sinusoidal features. A linear
    model trained on the resulting representation approximates a kernel
    machine at a fraction of the cost.

    The ``gamma`` parameter controls the bandwidth of the RBF kernel:
    ``K(x, y) = exp(-gamma * ||x - y||²)``. When set to ``"scale"``, it is
    computed from the training data as ``1 / (n_features * X.var())``.

    Output columns are typed as ``Float64`` in DashAI.

    Wraps ``sklearn.kernel_approximation.RBFSampler``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.kernel_approximation.RBFSampler.html
    - [2] Rahimi, A. & Recht, B. (2007). Random Features for Large-Scale Kernel
        Machines. Advances in Neural Information Processing Systems, 20.
    """

    SCHEMA = RBFSamplerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Approximates the feature map of an RBF kernel by Monte Carlo "
            "approximation of its Fourier transform."
        ),
        es=(
            "Aproxima el mapa de características de un kernel RBF mediante "
            "la aproximación de Monte Carlo de su transformada de Fourier."
        ),
        pt=(
            "Aproxima o mapa de características de um kernel RBF por "
            "aproximação de Monte Carlo de sua transformada de Fourier."
        ),
        de=(
            "Approximiert die Merkmalszuordnung eines RBF-Kernels durch "
            "Monte-Carlo-Approximation seiner Fourier-Transformation."
        ),
        zh="通过蒙特卡罗近似其傅里叶变换来近似 RBF 核的特征映射。",
    )
    DISPLAY_NAME = MultilingualString(
        en="RBF Sampler",
        es="Muestreador RBF",
        pt="Amostrador RBF",
        de="RBF-Stichprobennehmer",
        zh="RBF 采样器",
    )
    IMAGE_PREVIEW = "rbf_sampler.png"

    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialise the RBF sampler, resolving the ``"RandomState"`` sentinel.

        If ``random_state`` is the string ``"RandomState"``, a fresh
        ``numpy.random.RandomState`` instance is created in its place before
        being forwarded to sklearn's ``RBFSampler``.

        Parameters
        ----------
        **kwargs : dict
            random_state : int, ``"RandomState"``, or None, optional
                Seed for reproducibility.  The special string ``"RandomState"``
                generates a fresh random state. Default ``None``.
            Additional keys are forwarded to
            ``sklearn.kernel_approximation.RBFSampler``.
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
