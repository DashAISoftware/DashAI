from sklearn.decomposition import TruncatedSVD as TruncatedSVDOperation

from DashAI.back.api.utils import create_random_state
from DashAI.back.converters.category.dimensionality_reduction import (
    DimensionalityReductionConverter,
)
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


class TruncatedSVDSchema(BaseSchema):
    """Configuration schema for the TruncatedSVD converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.decomposition.TruncatedSVD``.
    """

    n_components: schema_field(
        int_field(gt=0),
        2,
        description=MultilingualString(
            en="Desired dimensionality of output data.",
            es="Dimensionalidad deseada de los datos de salida.",
            pt="Dimensionalidade desejada dos dados de saída.",
            de="Gewünschte Dimensionalität der Ausgabedaten.",
            zh="输出数据的目标维度。",
        ),
    )  # type: ignore
    algorithm: schema_field(
        enum_field(["arpack", "randomized"]),
        "randomized",
        description=MultilingualString(
            en="SVD solver to use.",
            es="Método SVD a utilizar.",
            pt="Solucionador SVD a usar.",
            de="Zu verwendender SVD-Löser.",
            zh="要使用的 SVD（奇异值分解）求解器。",
        ),
    )  # type: ignore
    n_iter: schema_field(
        int_field(gt=0),
        5,
        description=MultilingualString(
            en="Number of iterations for randomized SVD solver.",
            es="Número de iteraciones para el método SVD aleatorizado.",
            pt="Número de iterações para o solucionador SVD aleatorizado.",
            de="Anzahl der Iterationen für den randomisierten SVD-Löser.",
            zh="随机化 SVD 求解器的迭代次数。",
        ),
    )  # type: ignore
    n_oversamples: schema_field(
        int_field(gt=0),
        10,
        description=MultilingualString(
            en="Number of power iterations used in randomized SVD solver.",
            es=(
                "Número de iteraciones de potencia utilizadas en el método "
                "SVD aleatorizado."
            ),
            pt=(
                "Número de iterações de potência usadas no solucionador "
                "SVD aleatorizado."
            ),
            de=(
                "Anzahl der Potenziterationen, die im randomisierten SVD-Löser "
                "verwendet werden."
            ),
            zh="随机化 SVD 求解器中使用的过采样数量。",
        ),
    )  # type: ignore
    power_iteration_normalizer: schema_field(
        enum_field(["auto", "QR", "LU", "none"]),
        "auto",
        description=MultilingualString(
            en="Method to normalize the eigenvectors.",
            es="Método para normalizar los eigenvectores.",
            pt="Método para normalizar os autovetores.",
            de="Methode zur Normalisierung der Eigenvektoren.",
            zh="对特征向量进行归一化的方法。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(union_type(int_field(), enum_field(["RandomState"]))),
        None,
        description=MultilingualString(
            en=(
                "Used during randomized svd. Pass an int for reproducible "
                "results across multiple function calls."
            ),
            es=(
                "Usado durante SVD aleatorizado. Pasa un entero para obtener "
                "resultados reproducibles en múltiples ejecuciones."
            ),
            pt=(
                "Usado durante SVD aleatorizado. Passe um inteiro para obter "
                "resultados reproduzíveis em múltiplas execuções."
            ),
            de=(
                "Wird bei randomisiertem SVD verwendet. Ganzzahl übergeben für "
                "reproduzierbare Ergebnisse bei mehreren Funktionsaufrufen."
            ),
            zh="随机化 SVD 时使用。传入整数以获得可重现的结果。",
        ),
    )  # type: ignore
    tol: schema_field(
        float_field(ge=0),
        0.0,
        description=MultilingualString(
            en="Tolerance for ARPACK.",
            es="Tolerancia para ARPACK.",
            pt="Tolerância para ARPACK.",
            de="Toleranz für ARPACK.",
            zh="ARPACK 的容差。",
        ),
    )  # type: ignore


class TruncatedSVD(
    DimensionalityReductionConverter, SklearnWrapper, TruncatedSVDOperation
):
    """Reduce dimensionality using Truncated Singular Value Decomposition (LSA).

    TruncatedSVD performs linear dimensionality reduction by computing the
    thin SVD of the data matrix X, retaining only the top ``n_components``
    singular values and their associated left and right singular vectors:
    X ≈ U_k Σ_k V_k^T. The transformed data is X_new = X V_k.

    Unlike PCA, TruncatedSVD does not center the data before decomposition.
    This is crucial for sparse matrices such as TF-IDF or bag-of-words
    representations, where centering would introduce a dense intermediate matrix
    and destroy memory efficiency. In the text-mining community this algorithm
    is often called Latent Semantic Analysis (LSA).

    Key properties:

    - Works on both dense and sparse input matrices.
    - No mean centering: safe for high dimensional sparse data.
    - Supports a randomized solver (fast, approximate) and ARPACK (exact).
    - The ``n_oversamples`` and ``power_iteration_normalizer`` parameters
      control the accuracy-speed trade-off of the randomized solver.

    Wraps scikit-learn's ``TruncatedSVD``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html
    """

    SCHEMA = TruncatedSVDSchema
    DESCRIPTION = MultilingualString(
        en=(
            "This transformer performs linear dimensionality reduction by means "
            "of truncated singular value decomposition (SVD). Contrary to PCA, "
            "this estimator does not center the data before computing the "
            "singular value decomposition. This means it can work with sparse "
            "matrices efficiently."
        ),
        es=(
            "Este transformador realiza reducción lineal de dimensionalidad por "
            "medio de la descomposición en valores singulares truncada (SVD). "
            "A diferencia de PCA, este estimador no centra los datos antes de "
            "calcular la descomposición, lo que permite trabajar eficientemente "
            "con matrices dispersas."
        ),
        pt=(
            "Este transformador realiza redução linear de dimensionalidade por "
            "meio da decomposição em valores singulares truncada (SVD). "
            "Ao contrário do PCA, este estimador não centraliza os dados antes "
            "de calcular a decomposição, permitindo trabalhar eficientemente "
            "com matrizes esparsas."
        ),
        de=(
            "Dieser Transformator führt lineare Dimensionsreduktion mittels "
            "gekürzter Singulärwertzerlegung (SVD) durch. Im Gegensatz zu PCA "
            "zentriert dieser Schätzer die Daten nicht vor der Berechnung, "
            "was eine effiziente Arbeit mit sparse Matrizen ermöglicht."
        ),
        zh=(
            "该变换器通过截断奇异值分解（SVD）进行线性降维。"
            "与 PCA 不同，此估计器在计算奇异值分解前不对数据进行中心化，"
            "因此可以高效处理稀疏矩阵。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Dimensionality reduction using truncated SVD.",
        es="Reducción de dimensionalidad utilizando SVD truncado.",
        pt="Redução de dimensionalidade usando SVD Truncado.",
        de="Dimensionsreduktion mittels gekürzter SVD.",
        zh="使用截断 SVD（奇异值分解）进行降维。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Truncated SVD",
        es="SVD Truncado",
        pt="SVD Truncado",
        de="Gekürzte SVD",
        zh="截断 SVD",
    )
    IMAGE_PREVIEW = "truncated_svd.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs):
        """Initialize the TruncatedSVD converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        self.random_state = kwargs.pop("random_state", None)
        if self.random_state == "RandomState":
            self.random_state = create_random_state()
        kwargs["random_state"] = self.random_state

        # scikit-learn spells the QR-decomposition normalizer "OR" and rejects
        # "QR" (verified on 1.7.2: its StrOptions are {"auto","OR","LU","none"}).
        # That is a typo upstream, so the schema offers the correct name and the
        # misspelling is confined to this line. tests/back/
        # test_sklearn_option_validity.py pins it, and will tell us to remove
        # this if scikit-learn ever fixes the spelling.
        if kwargs.get("power_iteration_normalizer") == "QR":
            kwargs["power_iteration_normalizer"] = "OR"

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
