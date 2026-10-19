"""DashAI FAISS K-Means clustering model.

FAISS (Facebook AI Similarity Search) provides a highly optimised K-Means
implementation written in C++ that outperforms sklearn's on large datasets.
It uses the same Lloyd's algorithm but benefits from BLAS-level vectorisation.
GPU acceleration is available via faiss-gpu but requires additional setup;
the default installation (faiss-cpu) uses CPU only.

Install FAISS with: pip install faiss-cpu  (or faiss-gpu for GPU support)
"""

import numpy as np

from DashAI.back.core.schema_fields import (
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.faiss.faiss_like_clusterer import FaissLikeClusterer

if False:  # TYPE_CHECKING
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class FaissKMeansClusteringSchema(BaseSchema):
    """Schema that configures the FAISS K-Means clustering model."""

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
    max_iter: schema_field(
        int_field(ge=1),
        placeholder=300,
        description=MultilingualString(
            en="Maximum number of Lloyd's algorithm iterations.",
            es="Número máximo de iteraciones del algoritmo de Lloyd.",
            pt="Número máximo de iterações do algoritmo de Lloyd.",
            de="Maximale Anzahl an Iterationen des Lloyd-Algorithmus.",
            zh="Lloyd算法的最大迭代次数。",
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
            en="Random seed for centroid initialisation.",
            es="Semilla aleatoria para la inicialización de centroides.",
            pt="Semente aleatória para a inicialização dos centroides.",
            de="Zufallsstartwert für die Zentroiden-Initialisierung.",
            zh="用于质心初始化的随机种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore


class FaissKMeansClustering(FaissLikeClusterer):
    """FAISS K-Means clustering model for the Models module.

    FAISS K-Means applies Lloyd's algorithm in C++ with BLAS vectorisation and
    optional GPU acceleration. It converges substantially faster than sklearn's
    K-Means on large datasets (tens of thousands of samples or more) while
    producing equivalent cluster quality.

    Key hyperparameters: ``n_clusters`` (groups), ``max_iter`` (convergence
    budget), ``random_state`` (seed). Requires ``faiss-cpu`` or ``faiss-gpu``.

    References
    ----------
    - [1] Johnson, J., Douze, M., & Jégou, H. (2019). "Billion-scale similarity
           search with GPUs."
    - [2] https://github.com/facebookresearch/faiss
    """

    SCHEMA = FaissKMeansClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="FAISS K-Means",
        es="FAISS K-Means",
        pt="FAISS K-Means",
        de="FAISS K-Means",
        zh="FAISS K-均值",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "K-Means via FAISS — C++ vectorised and faster than sklearn "
            "on large datasets."
        ),
        es=(
            "K-Means vía FAISS — vectorización C++, más rápido que sklearn "
            "en datasets grandes."
        ),
        pt=(
            "K-Means via FAISS — vetorizado em C++, mais rápido que o sklearn "
            "em datasets grandes."
        ),
        de=(
            "K-Means über FAISS — C++-vektorisiert und schneller als sklearn "
            "bei großen Datensätzen."
        ),
        zh="通过FAISS实现的K-Means——C++向量化，在大型数据集上比sklearn更快。",
    )
    COLOR = "#66BB6A"
    ICON = "FlashOn"

    def __init__(
        self,
        n_clusters: int = 8,
        max_iter: int = 300,
        random_state: int = 0,
        **kwargs,
    ) -> None:
        """Initialise FAISS K-Means.

        Unlike sklearn-based models, the parameters must be received explicitly
        here because there is no underlying sklearn estimator class in the MRO
        that would capture and store them from **kwargs. FaissLikeClusterer,
        FaissLikeModel, ClusteringModel and BaseModel know nothing about
        n_clusters, max_iter or random_state — so this class must own them.

        Parameters
        ----------
        n_clusters : int
            Number of clusters. Must be >= 2.
        max_iter : int
            Maximum Lloyd's iterations. Must be >= 1.
        random_state : int
            Seed for centroid initialisation.
        **kwargs : dict
            Forwarded to parent classes (FaissLikeClusterer initialises
            self._labels and self._index from here).
        """
        super().__init__(**kwargs)
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.random_state = random_state
        # Fitted state — populated by train(), used by properties.
        # The faiss.Kmeans object itself is NOT stored on self because it is a
        # C++ object that is not picklable. We extract what we need right after
        # training and discard it.
        self._centroids: "np.ndarray | None" = None
        self._final_inertia: "float | None" = None

    def train(self, x_train: "DashAIDataset") -> "FaissKMeansClustering":
        """Fit FAISS K-Means and store cluster assignments.

        The faiss.Kmeans object is used only during this method. After training
        the fitted centroids and final SSE are extracted as plain numpy values,
        and the FAISS index (self._index) is retained for future label queries.
        The faiss.Kmeans object itself goes out of scope immediately so there
        is nothing non-picklable left on self.

        Parameters
        ----------
        x_train : DashAIDataset
            Input feature matrix.

        Returns
        -------
        FaissKMeansClustering
            The fitted model instance.

        Raises
        ------
        ImportError
            If the ``faiss`` package is not installed.
        """
        faiss = self._import_faiss()

        x = self._to_float32(x_train)
        d = x.shape[1]

        kmeans = faiss.Kmeans(
            d,
            self.n_clusters,
            niter=self.max_iter,
            seed=self.random_state,
            verbose=False,
        )
        kmeans.train(x)

        # Extract everything we need before kmeans goes out of scope.
        self._index = kmeans.index
        self._centroids = kmeans.centroids.copy()
        self._final_inertia = float(kmeans.obj[-1])

        _, assignments = self._index.search(x, 1)
        self._labels = assignments.flatten().astype(np.int64)
        return self

    def get_cluster_labels(self, x: "DashAIDataset | None" = None) -> np.ndarray:
        """Return fitted labels or assign new samples to nearest centroid.

        Parameters
        ----------
        x : DashAIDataset, optional
            New samples to assign. If omitted, returns labels from training.

        Returns
        -------
        numpy.ndarray
            Cluster label per sample.
        """
        if x is not None and self._index is not None:
            x_arr = self._to_float32(x)
            _, assignments = self._index.search(x_arr, 1)
            return assignments.flatten().astype(np.int64)

        if self._labels is None:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before returning labels."
            )
        return self._labels

    def get_fit_attributes(self) -> dict:
        """Return FAISS K-Means post-fit attributes for the converter report."""
        return {
            "cluster_centers": self._centroids.tolist(),
            "inertia": self._final_inertia,
        }

    @property
    def cluster_centers_(self) -> np.ndarray:
        """Fitted cluster centroids, shape (n_clusters, n_features).

        Raises AttributeError (not ValueError) so that hasattr() returns False
        before fitting — the clustering converter checks hasattr() to decide
        whether to export centroids in the run metadata.
        """
        if self._centroids is None:
            raise AttributeError(f"{self.__class__.__name__} has not been fitted.")
        return self._centroids

    @property
    def inertia_(self) -> float:
        """Final SSE objective value from the FAISS training run."""
        if self._final_inertia is None:
            raise AttributeError(f"{self.__class__.__name__} has not been fitted.")
        return self._final_inertia
