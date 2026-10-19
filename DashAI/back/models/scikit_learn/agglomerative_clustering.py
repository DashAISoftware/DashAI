"""DashAI Agglomerative (Hierarchical) clustering model."""

from sklearn.cluster import AgglomerativeClustering as _AgglomerativeClustering

from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_clusterer import (
    SklearnLikeClusterer,
)


class AgglomerativeClusteringSchema(BaseSchema):
    """Schema that configures the Agglomerative clustering model.

    Agglomerative clustering builds a hierarchy by iteratively merging the
    pair of clusters that minimises the chosen linkage criterion. It does not
    require specifying the number of clusters in advance when a dendrogram is
    analysed, but exposing ``n_clusters`` lets the user cut the hierarchy at a
    desired level.
    """

    n_clusters: schema_field(
        int_field(ge=2),
        placeholder=2,
        description=MultilingualString(
            en="Number of clusters to find.",
            es="Número de clusters a encontrar.",
            pt="Número de clusters a encontrar.",
            de="Anzahl der zu findenden Cluster.",
            zh="要查找的聚类数量。",
        ),
        alias=MultilingualString(
            en="Clusters", es="Clusters", pt="Clusters", de="Cluster", zh="聚类数"
        ),
    )  # type: ignore
    linkage: schema_field(
        enum_field(["ward", "complete", "average", "single"]),
        "ward",
        description=MultilingualString(
            en=(
                "Linkage criterion determining which distances to use between "
                "clusters. 'ward' minimises variance and only supports "
                "'euclidean' metric."
            ),
            es=(
                "Criterio de enlace que determina la distancia entre clusters. "
                "'ward' minimiza la varianza y solo admite la métrica 'euclidean'."
            ),
            pt=(
                "Critério de ligação que determina a distância entre clusters. "
                "'ward' minimiza a variância e admite apenas a métrica 'euclidean'."
            ),
            de=(
                "Linkage-Kriterium, das die Distanz zwischen Clustern bestimmt. "
                "'ward' minimiert die Varianz und unterstützt nur die "
                "'euclidean'-Metrik."
            ),
            zh="决定聚类间使用哪种距离的链接准则。'ward'最小化方差，仅支持'euclidean'度量。",
        ),
        alias=MultilingualString(
            en="Linkage", es="Enlace", pt="Ligação", de="Linkage", zh="链接方式"
        ),
    )  # type: ignore
    metric: schema_field(
        enum_field(["euclidean", "manhattan", "cosine"]),
        "euclidean",
        description=MultilingualString(
            en=(
                "Distance metric used to compute linkage. "
                "'ward' linkage only supports 'euclidean'."
            ),
            es=(
                "Métrica de distancia usada para el enlace. "
                "El enlace 'ward' solo admite 'euclidean'."
            ),
            pt=(
                "Métrica de distância usada para a ligação. "
                "A ligação 'ward' admite apenas 'euclidean'."
            ),
            de=(
                "Distanzmetrik zur Berechnung des Linkage. "
                "'ward'-Linkage unterstützt nur 'euclidean'."
            ),
            zh="用于计算链接的距离度量。'ward'链接仅支持'euclidean'。",
        ),
        alias=MultilingualString(
            en="Metric", es="Métrica", pt="Métrica", de="Metrik", zh="度量"
        ),
    )  # type: ignore
    compute_distances: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Whether to compute and store merge distances during fitting. "
                "Required to render a dendrogram. Has a small memory cost "
                "proportional to the number of samples."
            ),
            es=(
                "Si se calculan y almacenan las distancias de fusión durante el "
                "ajuste. Necesario para renderizar el dendrograma. Tiene un "
                "pequeño costo de memoria proporcional al número de muestras."
            ),
            pt=(
                "Se as distâncias de fusão são calculadas e armazenadas durante o "
                "ajuste. Necessário para renderizar o dendrograma. Tem um pequeno "
                "custo de memória proporcional ao número de amostras."
            ),
            de=(
                "Ob Fusionsdistanzen während der Anpassung berechnet und "
                "gespeichert werden. Erforderlich zur Darstellung eines "
                "Dendrogramms. Verursacht geringe, zur Stichprobenzahl "
                "proportionale Speicherkosten."
            ),
            zh="是否在拟合过程中计算并存储合并距离。渲染树状图时需要此项，会带来与样本数成正比的少量内存开销。",
        ),
        alias=MultilingualString(
            en="Compute distances",
            es="Calcular distancias",
            pt="Calcular distâncias",
            de="Distanzen berechnen",
            zh="计算距离",
        ),
    )  # type: ignore


class AgglomerativeClustering(SklearnLikeClusterer, _AgglomerativeClustering):
    """Agglomerative hierarchical clustering model for the Models module.

    Agglomerative clustering is a bottom-up hierarchical algorithm. Each sample
    starts as its own cluster; clusters are merged successively according to the
    chosen ``linkage`` criterion until ``n_clusters`` groups remain. The
    algorithm exposes cluster labels for comparison metrics such as Silhouette,
    Davies-Bouldin, and Calinski-Harabasz.

    Key hyperparameters include ``n_clusters`` (cut level of the hierarchy),
    ``linkage`` (merge strategy), and ``metric`` (distance function). The
    implementation wraps scikit-learn's ``AgglomerativeClustering`` estimator.

    References
    ----------
    - [1] Ward, J. H. (1963). "Hierarchical grouping to optimize an objective
           function."
    - [2] https://scikit-learn.org/stable/modules/generated/
           sklearn.cluster.AgglomerativeClustering.html
    """

    SCHEMA = AgglomerativeClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="Agglomerative",
        es="Aglomerativo",
        pt="Aglomerativo",
        de="Agglomerativ",
        zh="层次聚类",
    )
    DESCRIPTION = MultilingualString(
        en="Hierarchical clustering by progressively merging groups.",
        es="Clustering jerárquico que fusiona grupos progresivamente.",
        pt="Clustering hierárquico que funde grupos progressivamente.",
        de="Hierarchisches Clustering durch schrittweises Zusammenführen von Gruppen.",
        zh="通过逐步合并分组实现层次聚类。",
    )
    COLOR = "#42A5F5"
    ICON = "AccountTree"

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
        """Return Agglomerative post-fit attributes for the converter report."""
        distances = (
            self.distances_.tolist()
            if hasattr(self, "distances_")
            else list(range(len(self.children_)))
        )
        return {
            "linkage_data": {
                "children": self.children_.tolist(),
                "distances": distances,
                "n_leaves": len(self._labels),
            }
        }
