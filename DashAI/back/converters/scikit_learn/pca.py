from sklearn.decomposition import PCA as PCAOPERATION

from DashAI.back.api.utils import create_random_state
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
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class PCASchema(BaseSchema):
    """Configuration schema for the PCA converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.decomposition.PCA``.
    """

    n_components: schema_field(
        none_type(
            union_type(
                union_type(int_field(ge=1), float_field(gt=0.0, lt=1.0)),
                enum_field(["mle"]),
            ),
        ),
        2,
        description=MultilingualString(
            en="Number of components to keep. If None, all components are kept.",
            es=(
                "Número de componentes a conservar. Si es None, se conservan "
                "todas las componentes."
            ),
            pt=(
                "Número de componentes a manter. Se None, todos os componentes "
                "são mantidos."
            ),
            de=(
                "Anzahl der beizubehaltenden Komponenten. Wenn None, werden alle "
                "Komponenten behalten."
            ),
            zh="要保留的成分数量。如果为 None，则保留所有成分。",
        ),
    )  # type: ignore
    whiten: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "When True the components_ are scaled to ensure uncorrelated "
                "outputs with unit variances. May improve downstream estimators."
            ),
            es=(
                "Cuando es True las componentes se escalan para asegurar salidas "
                "no correlacionadas con varianzas unitarias. Puede mejorar "
                "estimadores posteriores."
            ),
            pt=(
                "Quando True, os componentes são escalonados para garantir saídas "
                "não correlacionadas com variâncias unitárias. Pode melhorar "
                "estimadores posteriores."
            ),
            de=(
                "Wenn True werden die Komponenten skaliert, um unkorrelierte "
                "Ausgaben mit Einheitsvarianz zu gewährleisten. Kann nachgelagerte "
                "Schätzer verbessern."
            ),
            zh="为 True 时，缩放成分以确保输出不相关且方差为 1，可提升后续估计器性能。",
        ),
    )  # type: ignore
    svd_solver: schema_field(
        enum_field(["auto", "full", "covariance_eigh", "arpack", "randomized"]),
        "auto",
        description=MultilingualString(
            en=(
                "Solver to use for eigendecomposition. 'auto' elige el más "
                "apropiado según los datos."
            ),
            es=(
                "Método para la descomposición propia. 'auto' elige el más "
                "apropiado según los datos."
            ),
            pt=(
                "Solucionador para a decomposição espectral. 'auto' escolhe o "
                "mais adequado para os dados."
            ),
            de=(
                "Löser für die Eigenzerlegung. 'auto' wählt den am besten "
                "geeigneten entsprechend der Daten."
            ),
            zh="用于特征分解的求解器。'auto' 根据数据自动选择最合适的求解器。",
        ),
    )  # type: ignore
    tol: schema_field(
        float_field(ge=0.0),
        0.0,
        description=MultilingualString(
            en="Tolerance for singular values when svd_solver == 'arpack'.",
            es="Tolerancia para valores singulares cuando svd_solver == 'arpack'.",
            pt="Tolerância para valores singulares quando svd_solver == 'arpack'.",
            de="Toleranz für Singulärwerte wenn svd_solver == 'arpack'.",
            zh="svd_solver == 'arpack' 时奇异值的容差。",
        ),
    )  # type: ignore
    iterated_power: schema_field(
        union_type(int_field(ge=1), enum_field(["auto"])),
        "auto",
        description=MultilingualString(
            en=(
                "Number of iterations for the power method when "
                "svd_solver == 'randomized'."
            ),
            es=(
                "Número de iteraciones para el método de potencia cuando "
                "svd_solver == 'randomized'."
            ),
            pt=(
                "Número de iterações para o método de potência quando "
                "svd_solver == 'randomized'."
            ),
            de=(
                "Anzahl der Iterationen für die Potenzmethode wenn "
                "svd_solver == 'randomized'."
            ),
            zh="svd_solver == 'randomized' 时幂方法的迭代次数。",
        ),
    )  # type: ignore
    n_oversamples: schema_field(
        int_field(ge=1),
        10,
        description=MultilingualString(
            en="Number of power iterations used when svd_solver == 'randomized'.",
            es="Número de iteraciones de potencia cuando svd_solver == 'randomized'.",
            pt=(
                "Número de iterações de potência usadas quando "
                "svd_solver == 'randomized'."
            ),
            de="Anzahl der Potenziterationen wenn svd_solver == 'randomized'.",
            zh="svd_solver == 'randomized' 时使用的过采样数量。",
        ),
    )  # type: ignore
    power_iteration_normalizer: schema_field(
        none_type(enum_field(["auto", "QR", "LU"])),
        "auto",
        description=MultilingualString(
            en=(
                "How the power iteration normalizer should be computed: 'auto', "
                "QR o LU. No usado por ARPACK."
            ),
            es=(
                "Cómo se calcula el normalizador de iteración de potencia: "
                "'auto', QR o LU. No se usa con ARPACK."
            ),
            pt=(
                "Como o normalizador de iteração de potência deve ser calculado: "
                "'auto', QR ou LU. Não usado com ARPACK."
            ),
            de=(
                "Wie der Potenziterations-Normalisierer berechnet werden soll: 'auto', "
                "QR oder LU. Nicht verwendet von ARPACK."
            ),
            zh="幂迭代归一化器的计算方式：'auto'、QR 或 LU。ARPACK 不使用此参数。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(union_type(int_field(), enum_field(["RandomState"]))),
        None,
        description=MultilingualString(
            en=(
                "Used when 'arpack' or 'randomized' solvers are used. Pass an int "
                "for reproducible results."
            ),
            es=(
                "Usado con los métodos 'arpack' o 'randomized'. Pasa un entero "
                "para resultados reproducibles."
            ),
            pt=(
                "Usado com os solucionadores 'arpack' ou 'randomized'. Passe um "
                "inteiro para resultados reproduzíveis."
            ),
            de=(
                "Wird verwendet wenn 'arpack' oder 'randomized' Löser verwendet werden."
                "Übergeben Sie eine Ganzzahl für reproduzierbare Ergebnisse."
            ),
            zh=(
                "使用 'arpack' 或 'randomized' 求解器时使用。"
                "传入整数以获得可重现的结果。"
            ),
        ),
    )  # type: ignore


class PCA(DimensionalityReductionConverter, SklearnWrapper, PCAOPERATION):
    """Reduce dimensionality using Principal Component Analysis (PCA).

    PCA finds a set of orthogonal axes (principal components) that successively
    capture the greatest amount of variance in the data. Given a centered data
    matrix X of shape (n_samples, n_features), the method computes the
    eigen-decomposition of the covariance matrix X^T X / (n-1), retaining only
    the top ``n_components`` eigenvectors. The data are then projected onto this
    lower dimensional subspace.

    PCA is well suited for preprocessing high dimensional continuous data before
    applying machine learning models, for visualisation of multivariate datasets,
    and for noise reduction. The ``whiten`` option rescales each component to
    unit variance, which can improve the performance of downstream estimators that
    assume spherical features (e.g. RBF-kernel SVMs).

    Key properties:

    - Linear, unsupervised transformation.
    - Components are ordered by descending explained variance.
    - Setting ``n_components`` to a float in (0, 1) automatically selects the
      number of components needed to explain that fraction of total variance.
    - ``n_components='mle'`` uses Minka's MLE to estimate the intrinsic
      dimensionality of the data.
    - Supports full, randomized, and ARPACK solvers for scalability.

    Wraps scikit-learn's ``PCA``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
    - [2] Pearson, K. (1901). "On lines and planes of closest fit to systems of
        points in space." Philosophical Magazine, 2(11), 559-572.
    - [3] Hotelling, H. (1933). "Analysis of a complex of statistical variables
        into principal components." Journal of Educational Psychology, 24(6),
        417-441.
    """

    SCHEMA = PCASchema
    DESCRIPTION = MultilingualString(
        en=(
            "Principal Component Analysis (PCA) is a dimensionality reduction "
            "technique used to simplify complex datasets while retaining as much "
            "variability as possible."
        ),
        es=(
            "El Análisis de Componentes Principales (PCA) es una técnica de "
            "reducción de dimensionalidad usada para simplificar conjuntos de "
            "datos complejos conservando tanta variabilidad como sea posible."
        ),
        pt=(
            "A Análise de Componentes Principais (PCA) é uma técnica de "
            "redução de dimensionalidade usada para simplificar conjuntos de "
            "dados complexos conservando o máximo de variabilidade possível."
        ),
        de=(
            "Hauptkomponentenanalyse (PCA) ist eine Dimensionsreduktions-"
            "technik, die zur Vereinfachung komplexer Datensätze verwendet wird, "
            "während so viel Variabilität wie möglich erhalten bleibt."
        ),
        zh=(
            "主成分分析（PCA）是一种降维技术，用于简化复杂数据集，"
            "同时尽可能保留最多的变异性。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Dimensionality reduction using PCA.",
        es="Reducción de dimensionalidad usando PCA.",
        pt="Redução de dimensionalidade usando PCA.",
        de="Dimensionsreduktion mittels PCA.",
        zh="使用 PCA（主成分分析）进行降维。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Principal Component Analysis (PCA)",
        es="Análisis de Componentes Principales (PCA)",
        pt="Análise de Componentes Principais (PCA)",
        de="Hauptkomponentenanalyse (PCA)",
        zh="PCA（主成分分析）",
    )
    IMAGE_PREVIEW = "pca.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the PCA converter.

        Handles the ``"RandomState"`` sentinel for ``random_state`` by converting
        it to a new ``numpy.RandomState`` instance at initialization time.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching ``PCASchema`` fields.
            If ``random_state`` is ``"RandomState"``, a fresh ``numpy.RandomState``
            instance is created automatically.
        """
        self.random_state = kwargs.pop("random_state", None)
        if self.random_state == "RandomState":
            self.random_state = create_random_state()
        kwargs["random_state"] = self.random_state

        super().__init__(**kwargs)

    def fit(self, x, y=None):
        x_pandas = x.to_pandas() if hasattr(x, "to_pandas") else x
        n_samples, n_features = x_pandas.shape
        max_components = min(n_samples, n_features)
        if isinstance(self.n_components, int) and self.n_components > max_components:
            raise ValueError(
                f"n_components={self.n_components} exceeds "
                f"min(n_samples, n_features)={max_components}. "
                f"Reduce n_components to at most {max_components}, "
                "or select more columns in the converter scope."
            )
        return super().fit(x, y)

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
