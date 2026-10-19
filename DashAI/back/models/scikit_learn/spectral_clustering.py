"""DashAI Spectral clustering model."""

from sklearn.cluster import SpectralClustering as _SpectralClustering

from DashAI.back.core.schema_fields import (
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_clusterer import (
    SklearnLikeClusterer,
)


class SpectralClusteringSchema(BaseSchema):
    """Schema that configures the Spectral clustering model.

    Spectral clustering constructs an affinity graph from the data, computes
    its leading eigenvectors, and partitions the resulting low-dimensional
    representation. It excels at finding clusters with non-convex shapes that
    defeat centroid-based algorithms.
    """

    n_clusters: schema_field(
        int_field(ge=2),
        placeholder=8,
        description=MultilingualString(
            en="Number of clusters to form.",
            es="Número de clusters a formar.",
            pt="Número de clusters a formar.",
            de="Anzahl der zu bildenden Cluster.",
            zh="要形成的聚类数量。",
        ),
        alias=MultilingualString(
            en="Clusters", es="Clusters", pt="Clusters", de="Cluster", zh="聚类数"
        ),
    )  # type: ignore
    affinity: schema_field(
        enum_field(["rbf", "nearest_neighbors", "cosine"]),
        "rbf",
        description=MultilingualString(
            en=(
                "Similarity measure used to construct the affinity graph. "
                "'rbf' uses a Gaussian kernel controlled by 'gamma'."
            ),
            es=(
                "Medida de similitud para construir el grafo de afinidad. "
                "'rbf' usa un kernel gaussiano controlado por 'gamma'."
            ),
            pt=(
                "Medida de similaridade usada para construir o grafo de afinidade. "
                "'rbf' usa um kernel gaussiano controlado por 'gamma'."
            ),
            de=(
                "Ähnlichkeitsmaß zur Konstruktion des Affinitätsgraphen. "
                "'rbf' verwendet einen Gauß-Kernel, gesteuert über 'gamma'."
            ),
            zh="用于构建亲和图的相似性度量。'rbf'使用由'gamma'控制的高斯核。",
        ),
        alias=MultilingualString(
            en="Affinity", es="Afinidad", pt="Afinidade", de="Affinität", zh="亲和度"
        ),
    )  # type: ignore
    gamma: schema_field(
        float_field(gt=0.0),
        placeholder=1.0,
        description=MultilingualString(
            en=(
                "Kernel coefficient for the 'rbf' affinity. "
                "Ignored for other affinities."
            ),
            es=(
                "Coeficiente del kernel para la afinidad 'rbf'. "
                "Se ignora para otras afinidades."
            ),
            pt=(
                "Coeficiente do kernel para a afinidade 'rbf'. "
                "Ignorado para outras afinidades."
            ),
            de=(
                "Kernel-Koeffizient für die 'rbf'-Affinität. "
                "Wird für andere Affinitäten ignoriert."
            ),
            zh="'rbf'亲和度的核系数。对其他亲和度类型无效。",
        ),
        alias=MultilingualString(
            en="Gamma", es="Gamma", pt="Gamma", de="Gamma", zh="Gamma"
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=0,
        description=MultilingualString(
            en=(
                "Random seed for eigenvector decomposition and k-means initialisation."
            ),
            es=(
                "Semilla aleatoria para la descomposición de "
                "eigenvectores e inicialización de k-means."
            ),
            pt=(
                "Semente aleatória para a decomposição de autovetores "
                "e inicialização do k-means."
            ),
            de=(
                "Zufallsstartwert für die Eigenvektorzerlegung und die "
                "K-Means-Initialisierung."
            ),
            zh="用于特征向量分解和k-means初始化的随机种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore


class SpectralClustering(SklearnLikeClusterer, _SpectralClustering):
    """Spectral clustering model for the Models module.

    Spectral clustering applies eigenvalue decomposition to an affinity matrix
    derived from the input data. It can detect clusters of arbitrary shape by
    leveraging graph-theoretic connectivity. Because it does not expose a
    ``predict`` method, cluster labels for new samples cannot be inferred
    without re-fitting.

    Key hyperparameters include ``n_clusters`` (partitions of the spectral
    embedding), ``affinity`` (graph construction method), ``gamma`` (RBF kernel
    width), and ``random_state`` (seed). The implementation wraps scikit-learn's
    ``SpectralClustering`` estimator.

    References
    ----------
    - [1] Ng, A. Y., Jordan, M. I., & Weiss, Y. (2002). "On spectral
           clustering: Analysis and an algorithm."
    - [2] https://scikit-learn.org/stable/modules/generated/
           sklearn.cluster.SpectralClustering.html
    """

    SCHEMA = SpectralClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="Spectral", es="Espectral", pt="Espectral", de="Spektral", zh="谱聚类"
    )
    DESCRIPTION = MultilingualString(
        en="Graph-based clustering via eigenvalue decomposition.",
        es="Clustering basado en grafos mediante descomposición de eigenvalores.",
        pt="Clustering baseado em grafos por meio de decomposição de autovalores.",
        de="Graphbasiertes Clustering mittels Eigenwertzerlegung.",
        zh="通过特征值分解实现的基于图的聚类方法。",
    )
    COLOR = "#EC407A"
    ICON = "Grain"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper. See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
