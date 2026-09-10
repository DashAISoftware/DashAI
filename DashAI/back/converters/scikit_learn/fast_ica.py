from sklearn.decomposition import FastICA as FastICAOperation

from DashAI.back.api.utils import (
    create_random_state,
    parse_string_to_dict,
    parse_string_to_list,
)
from DashAI.back.converters.category.dimensionality_reduction import (
    DimensionalityReductionConverter,
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
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class FastICASchema(BaseSchema):
    """Configuration schema for the FastICA converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.decomposition.FastICA``.
    """

    n_components: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en="Number of components to extract.",
            es="Número de componentes a extraer.",
            pt="Número de componentes a extrair.",
            de="Anzahl der zu extrahierenden Komponenten.",
            zh="要提取的成分数量。",
        ),
    )  # type: ignore
    algorithm: schema_field(
        enum_field(["parallel", "deflation"]),
        "parallel",
        description=MultilingualString(
            en="Apply parallel or deflational algorithm for FastICA.",
            es="Aplica el algoritmo paralelo o deflacional para FastICA.",
            pt="Aplicar algoritmo paralelo ou deflacional para FastICA.",
            de="Parallelen oder deflationären Algorithmus für FastICA anwenden.",
            zh="为 FastICA 应用并行或紧缩算法。",
        ),
    )  # type: ignore
    # Deprecated since version 1.1
    whiten: schema_field(
        none_type(
            union_type(
                enum_field(["arbitrary-variance", "unit-variance"]), bool_field()
            )
        ),
        "unit-variance",
        description=MultilingualString(
            en="If True, the data is whitened.",
            es="Si es True, los datos se blanquean.",
            pt="Se True, os dados são branqueados.",
            de="Wenn True, werden die Daten geweißt.",
            zh="如果为 True，则对数据进行白化处理。",
        ),
    )  # type: ignore
    fun: schema_field(
        enum_field(["logcosh", "exp", "cube"]),
        "logcosh",
        description=MultilingualString(
            en=(
                "Functional form of the G function used in the approximation "
                "to neg-entropy."
            ),
            es=(
                "Forma funcional de la función G utilizada en la aproximación "
                "a la neg-entropía."
            ),
            pt=("Forma funcional da função G usada na aproximação da neg-entropia."),
            de=(
                "Funktionale Form der G-Funktion, die bei der Annäherung an "
                "Neg-Entropie verwendet wird."
            ),
            zh="用于近似负熵的 G 函数的函数形式。",
        ),
    )  # type: ignore
    fun_args: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en="Arguments to the G function.",
            es="Argumentos de la función G.",
            pt="Argumentos da função G.",
            de="Argumente für die G-Funktion.",
            zh="G 函数的参数。",
        ),
    )  # type: ignore
    max_iter: schema_field(
        int_field(ge=1),
        200,
        description=MultilingualString(
            en="Maximum number of iterations to perform.",
            es="Número máximo de iteraciones a realizar.",
            pt="Número máximo de iterações a realizar.",
            de="Maximale Anzahl der durchzuführenden Iterationen.",
            zh="执行的最大迭代次数。",
        ),
    )  # type: ignore
    tol: schema_field(
        float_field(ge=0.0),
        1e-04,
        description=MultilingualString(
            en="Tolerance on update at each iteration.",
            es="Tolerancia en la actualización en cada iteración.",
            pt="Tolerância na atualização em cada iteração.",
            de="Toleranz bei der Aktualisierung in jeder Iteration.",
            zh="每次迭代更新的容差。",
        ),
    )  # type: ignore
    w_init: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en="Initial guess for the unmixing matrix.",
            es="Estimación inicial de la matriz de separación.",
            pt="Estimativa inicial para a matriz de separação.",
            de="Anfangsschätzung für die Trennungsmatrix.",
            zh="分离矩阵的初始猜测值。",
        ),
    )  # type: ignore
    whiten_solver: schema_field(
        enum_field(["eigh", "svd"]),
        "svd",
        description=MultilingualString(
            en="The solver to use for whitening.",
            es="Método a utilizar para el blanqueo.",
            pt="O solucionador a usar para o branqueamento.",
            de="Der zu verwendende Löser für die Weißung.",
            zh="用于白化的求解器。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(union_type(int_field(), enum_field(["RandomState"]))),
        None,
        description=MultilingualString(
            en=(
                "Used to initialize w_init when not specified, with a normal "
                "distribution. Pass an int for reproducible results."
            ),
            es=(
                "Usado para inicializar w_init cuando no se especifica, con "
                "una distribución normal. Pasa un entero para resultados "
                "reproducibles."
            ),
            pt=(
                "Usado para inicializar w_init quando não especificado, com "
                "uma distribuição normal. Passe um inteiro para resultados "
                "reproduzíveis."
            ),
            de=(
                "Zur Initialisierung von w_init verwendet, wenn nicht angegeben, "
                "mit einer Normalverteilung. Ganzzahl übergeben für reproduzierbare "
                "Ergebnisse."
            ),
            zh="未指定时用正态分布初始化 w_init。传入整数以获得可重现的结果。",
        ),
    )  # type: ignore


class FastICA(DimensionalityReductionConverter, SklearnWrapper, FastICAOperation):
    """Decompose features into statistically independent components using FastICA.

    Independent Component Analysis (ICA) models the observed data X as a linear
    mixture X = A S of latent source signals S that are assumed to be mutually
    statistically independent and non-Gaussian. FastICA recovers the unmixing
    matrix W = A^{-1} by maximising the non-Gaussianity of the projected
    components, using the fixed-point iteration algorithm of Hyvärinen & Oja.

    Typical applications include blind source separation (e.g. recovering
    individual audio signals from a mixture of microphone recordings), removal
    of artefacts from EEG/fMRI signals, and feature extraction for image
    processing where latent factors are expected to be non-Gaussian.

    Key properties:

    - Unsupervised: does not require labels.
    - The ``algorithm`` parameter selects between a fully parallel update
      (faster) and a sequential deflation strategy (more stable for some data).
    - The contrast function ``fun`` (logcosh, exp, or cube) controls the
      approximation to negentropy used as the independence criterion.
    - Data are whitened before ICA unless ``whiten=False``; the ``whiten_solver``
      parameter selects between an eigenvalue decomposition and SVD.
    - Component signs and ordering are arbitrary and may differ between runs.

    Wraps scikit-learn's ``FastICA``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html
    - [2] Hyvärinen, A. & Oja, E. (2000). "Independent Component Analysis:
        Algorithms and Applications." Neural Networks, 13(4-5), 411-430.
    """

    SCHEMA = FastICASchema
    N_COMPONENTS_FEATURES_BOUNDED: bool = False
    DESCRIPTION = MultilingualString(
        en="FastICA: a fast algorithm for Independent Component Analysis.",
        es=(
            "FastICA: un algoritmo rápido para "
            "el Análisis de Componentes Independientes."
        ),
        pt=(
            "FastICA: um algoritmo rápido para a Análise de Componentes Independentes."
        ),
        de="FastICA: ein schneller Algorithmus für die Unabhängige Komponentenanalyse.",
        zh="FastICA：一种快速的独立成分分析算法。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Fast ICA", es="Fast ICA", pt="Fast ICA", de="Fast ICA", zh="Fast ICA"
    )
    IMAGE_PREVIEW = "fast_ica.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the FastICA converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        self.fun_args = kwargs.pop("fun_args", None)
        if self.fun_args is not None:
            self.fun_args = parse_string_to_dict(self.fun_args)
        kwargs["fun_args"] = self.fun_args

        self.w_init = kwargs.pop("w_init", None)
        if self.w_init is not None:
            self.w_init = [parse_string_to_list(self.w_init)]
        kwargs["w_init"] = self.w_init

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
            Not used; all output columns share the
            same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Float type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
