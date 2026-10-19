"""DashAI HDBSCAN clustering model."""

from sklearn.cluster import HDBSCAN as _HDBSCAN

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


class HDBSCANClusteringSchema(BaseSchema):
    """Schema that configures the HDBSCAN clustering model.

    HDBSCAN extends DBSCAN by running it at multiple density thresholds and
    extracting the most stable clusters via a condensed cluster tree. It handles
    clusters of varying density, eliminates the manual ``eps`` parameter, and
    assigns soft cluster membership scores (``probabilities_``).
    """

    min_cluster_size: schema_field(
        int_field(ge=2),
        placeholder=5,
        description=MultilingualString(
            en="Minimum number of samples required to form a cluster.",
            es="Mínimo de muestras requeridas para formar un cluster.",
            pt="Número mínimo de amostras necessárias para formar um cluster.",
            de="Mindestanzahl an Stichproben, die zur Bildung eines Clusters "
            "erforderlich sind.",
            zh="形成一个聚类所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min cluster size",
            es="Tamaño mínimo de cluster",
            pt="Tamanho mínimo do cluster",
            de="Min. Clustergröße",
            zh="最小聚类大小",
        ),
    )  # type: ignore
    min_samples: schema_field(
        int_field(ge=1),
        placeholder=5,
        description=MultilingualString(
            en=(
                "Number of samples in a neighbourhood for a point "
                "to be considered a core point."
            ),
            es=(
                "Número de muestras en una vecindad para que un punto "
                "sea considerado central."
            ),
            pt=(
                "Número de amostras em uma vizinhança para que um ponto "
                "seja considerado central."
            ),
            de=(
                "Anzahl der Stichproben in einer Nachbarschaft, damit ein Punkt "
                "als Kernpunkt gilt."
            ),
            zh="使一个点被视为核心点所需邻域内的样本数。",
        ),
        alias=MultilingualString(
            en="Min samples",
            es="Mínimo de muestras",
            pt="Mínimo de amostras",
            de="Min. Stichproben",
            zh="最小样本数",
        ),
    )  # type: ignore
    metric: schema_field(
        enum_field(["euclidean", "manhattan", "cosine"]),
        "euclidean",
        description=MultilingualString(
            en="Distance metric used to compute core distances.",
            es="Métrica de distancia usada para calcular distancias centrales.",
            pt="Métrica de distância usada para calcular distâncias centrais.",
            de="Distanzmetrik zur Berechnung der Kernabstände.",
            zh="用于计算核心距离的距离度量。",
        ),
        alias=MultilingualString(
            en="Metric", es="Métrica", pt="Métrica", de="Metrik", zh="度量"
        ),
    )  # type: ignore


class HDBSCANClustering(SklearnLikeClusterer, _HDBSCAN):
    """HDBSCAN clustering model for the Models module.

    HDBSCAN is a hierarchical density-based unsupervised algorithm. It builds a
    minimum spanning tree over core distances, converts it to a cluster
    hierarchy, and selects the most persistent clusters. Noise samples are
    labelled ``-1``. Unlike DBSCAN, it supports clusters of varying density
    without requiring a global ``eps`` parameter.

    Key hyperparameters include ``min_cluster_size`` (smallest group accepted),
    ``min_samples`` (core-point threshold), and ``metric`` (distance function).
    Requires scikit-learn >= 1.3. The implementation wraps scikit-learn's
    ``HDBSCAN`` estimator.

    References
    ----------
    - [1] Campello, R. J. G. B., Moulavi, D., & Sander, J. (2013).
           "Density-Based Clustering Based on Hierarchical Density Estimates."
    - [2] https://scikit-learn.org/stable/modules/generated/
           sklearn.cluster.HDBSCAN.html
    """

    SCHEMA = HDBSCANClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="HDBSCAN", es="HDBSCAN", pt="HDBSCAN", de="HDBSCAN", zh="HDBSCAN"
    )
    DESCRIPTION = MultilingualString(
        en="Hierarchical density-based clustering with variable density support.",
        es="Clustering jerárquico basado en densidad con soporte de densidad variable.",
        pt="Clustering hierárquico baseado em densidade com suporte a densidade "
        "variável.",
        de="Hierarchisches dichtebasiertes Clustering mit Unterstützung "
        "variabler Dichte.",
        zh="支持可变密度的层次化基于密度的聚类方法。",
    )
    COLOR = "#26C6DA"
    ICON = "Layers"

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
        """Return HDBSCAN post-fit attributes for the converter report.

        sklearn's HDBSCAN does not expose ``cluster_persistence_``. Stability
        is approximated as the mean membership probability across samples
        assigned to each cluster (``probabilities_`` from sklearn).
        """
        import numpy as np

        attrs = {}
        labels = self._labels
        probabilities = getattr(self, "probabilities_", None)

        if labels is not None and probabilities is not None:
            unique_clusters = np.unique(labels[labels != -1])
            if len(unique_clusters) > 0:
                attrs["cluster_persistence"] = [
                    float(np.mean(probabilities[labels == lbl]))
                    for lbl in unique_clusters
                ]

        n_noise = int(np.sum(labels == -1)) if labels is not None else 0
        if n_noise > 0:
            attrs["n_noise_points"] = n_noise

        return attrs
