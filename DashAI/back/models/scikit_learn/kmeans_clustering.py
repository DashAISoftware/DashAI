"""DashAI K-Means clustering model."""

from sklearn.cluster import KMeans as _KMeans

from DashAI.back.core.schema_fields import (
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_clusterer import (
    SklearnLikeClusterer,
)


class KMeansClusteringSchema(BaseSchema):
    """Schema that configures the K-Means clustering model.

    K-Means partitions the dataset into a fixed number of clusters by
    iteratively assigning samples to the nearest centroid and updating each
    centroid as the mean of its assigned samples. It is appropriate when the
    expected number of compact, centroid-shaped groups is known in advance.
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
    init: schema_field(
        enum_field(["k-means++", "random"]),
        "k-means++",
        description=MultilingualString(
            en=(
                "Centroid initialisation method. 'k-means++' selects initial centroids "
                "to speed up convergence; 'random' picks them uniformly at random."
            ),
            es=(
                "Método de inicialización de centroides. "
                "'k-means++' selecciona centroides iniciales "
                "para acelerar la convergencia; 'random' los elige al azar."
            ),
            pt=(
                "Método de inicialização de centroides. 'k-means++' seleciona "
                "centroides iniciais para acelerar a convergência; 'random' os "
                "escolhe uniformemente ao acaso."
            ),
            de=(
                "Methode zur Initialisierung der Zentroiden. 'k-means++' wählt "
                "Startzentroiden zur schnelleren Konvergenz aus; 'random' wählt "
                "sie gleichverteilt zufällig."
            ),
            zh="质心初始化方法。'k-means++'选择初始质心以加快收敛；'random'均匀随机选取。",
        ),
        alias=MultilingualString(
            en="Init method",
            es="Método de inicio",
            pt="Método de inicialização",
            de="Init-Methode",
            zh="初始化方法",
        ),
    )  # type: ignore
    max_iter: schema_field(
        int_field(ge=1),
        placeholder=300,
        description=MultilingualString(
            en="Maximum number of iterations for a single run.",
            es="Número máximo de iteraciones por ejecución.",
            pt="Número máximo de iterações por execução.",
            de="Maximale Anzahl an Iterationen pro Durchlauf.",
            zh="单次运行的最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Iteraciones máximas",
            pt="Iterações máximas",
            de="Max. Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=0,
        description=MultilingualString(
            en="Random seed used by K-Means.",
            es="Semilla aleatoria usada por K-Means.",
            pt="Semente aleatória usada pelo K-Means.",
            de="Von K-Means verwendeter Zufallsstartwert.",
            zh="K-Means使用的随机种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore


class KMeansClustering(SklearnLikeClusterer, _KMeans):
    """K-Means clustering model for the Models module.

    K-Means is a centroid-based unsupervised algorithm. It fits ``n_clusters``
    centroids and assigns each sample to the closest centroid according to the
    Euclidean distance used by scikit-learn's implementation. The model exposes
    cluster labels for comparison metrics such as Silhouette,
    Davies-Bouldin, and Calinski-Harabasz.

    Key hyperparameters include ``n_clusters`` (the number of groups to form)
    and ``random_state`` (seed used for centroid initialisation). The
    implementation wraps scikit-learn's ``KMeans`` estimator.

    References
    ----------
    - [1] MacQueen, J. (1967). "Some methods for classification and analysis
           of multivariate observations."
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
    """

    SCHEMA = KMeansClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="K-Means", es="K-Means", pt="K-Means", de="K-Means", zh="K-均值"
    )
    DESCRIPTION = MultilingualString(
        en="Partitions samples into a fixed number of clusters.",
        es="Agrupa muestras en un número fijo de clusters.",
        pt="Particiona amostras em um número fixo de clusters.",
        de="Teilt Stichproben in eine feste Anzahl von Clustern auf.",
        zh="将样本划分为固定数量的聚类。",
    )
    COLOR = "#26A69A"
    ICON = "Hub"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper. See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)

    def get_fit_attributes(self) -> dict:
        """Return K-Means post-fit attributes for the converter report."""
        return {
            "cluster_centers": self.cluster_centers_.tolist(),
            "inertia": float(self.inertia_),
        }
