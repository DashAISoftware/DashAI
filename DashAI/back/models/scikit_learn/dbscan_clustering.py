"""DashAI DBSCAN clustering model."""

from sklearn.cluster import DBSCAN as _DBSCAN

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


class DBSCANClusteringSchema(BaseSchema):
    """Schema that configures the DBSCAN clustering model.

    DBSCAN groups samples by density. A point becomes a core point when at
    least ``min_samples`` points fall within distance ``eps`` under the selected
    metric. Dense regions become clusters and sparse points can be marked as
    noise.
    """

    eps: schema_field(
        float_field(gt=0.0),
        placeholder=0.5,
        description=MultilingualString(
            en="Maximum distance between two samples to be considered neighbours.",
            es="Distancia máxima entre dos muestras para considerarlas vecinas.",
            pt="Distância máxima entre duas amostras para serem consideradas vizinhas.",
            de=(
                "Maximaler Abstand zwischen zwei Stichproben, um als Nachbarn "
                "zu gelten."
            ),
            zh="两个样本被视为邻居的最大距离。",
        ),
        alias=MultilingualString(en="Eps", es="Eps", pt="Eps", de="Eps", zh="Eps"),
    )  # type: ignore
    min_samples: schema_field(
        int_field(ge=1),
        placeholder=5,
        description=MultilingualString(
            en="Minimum samples in a neighbourhood for a point to be core.",
            es="Mínimo de muestras en una vecindad para que un punto sea central.",
            pt="Mínimo de amostras em uma vizinhança para que um ponto seja central.",
            de="Mindestanzahl an Stichproben in einer Nachbarschaft, damit ein Punkt "
            "als Kernpunkt gilt.",
            zh="一个点成为核心点所需邻域内的最小样本数。",
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
            en="Distance metric used by DBSCAN.",
            es="Métrica de distancia usada por DBSCAN.",
            pt="Métrica de distância usada pelo DBSCAN.",
            de="Von DBSCAN verwendete Distanzmetrik.",
            zh="DBSCAN使用的距离度量。",
        ),
        alias=MultilingualString(
            en="Metric", es="Métrica", pt="Métrica", de="Metrik", zh="度量"
        ),
    )  # type: ignore


class DBSCANClustering(SklearnLikeClusterer, _DBSCAN):
    """DBSCAN clustering model for the Models module.

    DBSCAN is a density-based unsupervised algorithm that discovers clusters
    without requiring the number of clusters in advance. It is useful when
    groups have irregular shapes and when noise or outliers should be identified
    explicitly. Noise samples are labelled as ``-1`` by scikit-learn.

    Key hyperparameters include ``eps`` (the neighbourhood radius),
    ``min_samples`` (minimum points required to form a dense region), and
    ``metric`` (distance function). The implementation wraps scikit-learn's
    ``DBSCAN`` estimator.

    References
    ----------
    - [1] Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996).
           "A density-based algorithm for discovering clusters in large spatial
           databases with noise."
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
    """

    SCHEMA = DBSCANClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="DBSCAN", es="DBSCAN", pt="DBSCAN", de="DBSCAN", zh="DBSCAN"
    )
    DESCRIPTION = MultilingualString(
        en="Density-based clustering that can identify noise points.",
        es="Clustering basado en densidad que puede identificar puntos de ruido.",
        pt="Clustering baseado em densidade que pode identificar pontos de ruído.",
        de="Dichtebasiertes Clustering, das Rauschpunkte identifizieren kann.",
        zh="基于密度的聚类方法，能够识别噪声点。",
    )
    COLOR = "#7E57C2"
    ICON = "Radar"

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
        """Return DBSCAN post-fit attributes for the converter report."""
        import numpy as np

        n_noise = int(np.sum(self._labels == -1))
        return {"n_noise_points": n_noise}
