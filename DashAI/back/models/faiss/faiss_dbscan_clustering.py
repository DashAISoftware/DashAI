"""DashAI FAISS-accelerated DBSCAN clustering model.

This module demonstrates FAISS as an accelerator for a sklearn-style algorithm.

Standard DBSCAN (sklearn) is O(n²) for the epsilon-neighbourhood search: it
compares every point against every other point to find all neighbours within
distance eps. On a dataset of 100 000 samples that is 10 billion comparisons.

FAISS-DBSCAN replaces that bottleneck with an efficient range search on a FAISS
index.  ``IndexFlatL2.range_search(x, eps²)`` retrieves, for each point, all
vectors within squared-L2 distance eps² in a fraction of the time.  The DBSCAN
cluster-labelling logic (core points, BFS expansion, noise assignment) is then
applied to the resulting neighbour lists — exactly the same as the original
algorithm, just built on top of a much faster distance oracle.

Install FAISS with: pip install faiss-cpu  (or faiss-gpu for GPU support)
"""

import numpy as np

from DashAI.back.core.schema_fields import (
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.faiss.faiss_like_clusterer import FaissLikeClusterer

if False:  # TYPE_CHECKING
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class FaissDBSCANClusteringSchema(BaseSchema):
    """Schema that configures the FAISS-accelerated DBSCAN model.

    Parameters are identical to sklearn's DBSCAN. The only difference is that
    neighbourhood search is delegated to a FAISS IndexFlatL2 (Euclidean metric),
    making the algorithm practical on large datasets where sklearn's brute-force
    O(n²) search becomes a bottleneck.
    """

    eps: schema_field(
        float_field(gt=0.0),
        placeholder=0.5,
        description=MultilingualString(
            en=(
                "Maximum Euclidean distance between two samples to be "
                "considered neighbours."
            ),
            es=(
                "Distancia euclidiana máxima entre dos muestras para "
                "considerarlas vecinas."
            ),
            pt=(
                "Distância euclidiana máxima entre duas amostras para "
                "serem consideradas vizinhas."
            ),
            de=(
                "Maximaler euklidischer Abstand zwischen zwei Stichproben, um "
                "als Nachbarn zu gelten."
            ),
            zh="两个样本被视为邻居的最大欧氏距离。",
        ),
        alias=MultilingualString(en="Eps", es="Eps", pt="Eps", de="Eps", zh="Eps"),
    )  # type: ignore
    min_samples: schema_field(
        int_field(ge=1),
        placeholder=5,
        description=MultilingualString(
            en="Minimum samples in a neighbourhood for a point to be a core point "
            "(including the point itself).",
            es="Mínimo de muestras en una vecindad para que un punto sea central "
            "(incluido el propio punto).",
            pt="Mínimo de amostras em uma vizinhança para que um ponto seja "
            "central (incluindo o próprio ponto).",
            de="Mindestanzahl an Stichproben in einer Nachbarschaft, damit ein "
            "Punkt als Kernpunkt gilt (einschließlich des Punktes selbst).",
            zh="一个点成为核心点所需邻域内的最小样本数（含该点本身）。",
        ),
        alias=MultilingualString(
            en="Min samples",
            es="Mínimo de muestras",
            pt="Mínimo de amostras",
            de="Min. Stichproben",
            zh="最小样本数",
        ),
    )  # type: ignore


class FaissDBSCANClustering(FaissLikeClusterer):
    """FAISS-accelerated DBSCAN clustering model for the Models module.

    Replaces sklearn DBSCAN's O(n²) epsilon-neighbourhood search with FAISS
    ``IndexFlatL2.range_search``, which uses BLAS-optimised distance
    computation. The cluster-labelling step (core-point detection, BFS
    expansion, noise assignment) is identical to the original algorithm and
    is implemented in pure Python/NumPy.

    Noise samples receive label ``-1``, the same convention as sklearn DBSCAN
    and sklearn HDBSCAN. The algorithm does not require specifying the number
    of clusters in advance.

    Key hyperparameters: ``eps`` (neighbourhood radius), ``min_samples``
    (core-point threshold). Only the Euclidean (L2) metric is supported
    because FAISS ``IndexFlatL2`` computes squared L2 distances.

    References
    ----------
    - [1] Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996).
           "A density-based algorithm for discovering clusters in large
           spatial databases with noise."
    - [2] Johnson, J., Douze, M., & Jégou, H. (2019). "Billion-scale
           similarity search with GPUs."
    - [3] https://github.com/facebookresearch/faiss
    """

    SCHEMA = FaissDBSCANClusteringSchema
    DISPLAY_NAME = MultilingualString(
        en="FAISS-DBSCAN",
        es="FAISS-DBSCAN",
        pt="FAISS-DBSCAN",
        de="FAISS-DBSCAN",
        zh="FAISS-DBSCAN",
    )
    DESCRIPTION = MultilingualString(
        en="DBSCAN with FAISS-accelerated neighbourhood search for large datasets.",
        es="DBSCAN con búsqueda de vecindad acelerada por FAISS para datasets grandes.",
        pt="DBSCAN com busca de vizinhança acelerada por FAISS para datasets grandes.",
        de="DBSCAN mit FAISS-beschleunigter Nachbarschaftssuche für große Datensätze.",
        zh="使用FAISS加速邻域搜索的DBSCAN，适用于大型数据集。",
    )
    COLOR = "#FFA726"
    ICON = "Bolt"

    def __init__(
        self,
        eps: float = 0.5,
        min_samples: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.eps = eps
        self.min_samples = min_samples

    def get_fit_attributes(self) -> dict:
        """Return FAISS-DBSCAN post-fit attributes for the converter report."""
        n_noise = int(np.sum(self._labels == -1))
        return {"n_noise_points": n_noise} if n_noise > 0 else {}

    def train(self, x_train: "DashAIDataset") -> "FaissDBSCANClustering":
        """Fit FAISS-DBSCAN: build index, run range search, label clusters.

        The neighbourhood search uses ``IndexFlatL2.range_search(x, eps²)``.
        FAISS computes squared Euclidean distances, so the threshold passed
        to ``range_search`` is ``eps ** 2``, not ``eps``.

        The query point itself is always returned as its own neighbour
        (distance 0), so ``min_samples=5`` means a point needs 4 additional
        neighbours within ``eps`` to become a core point — matching sklearn's
        convention exactly.

        Parameters
        ----------
        x_train : DashAIDataset
            Input feature matrix.

        Returns
        -------
        FaissDBSCANClustering
            The fitted model instance.

        Raises
        ------
        ImportError
            If the ``faiss`` package is not installed.
        """
        faiss = self._import_faiss()

        x = self._to_float32(x_train)
        n, d = x.shape

        # Build exact L2 index and add all points
        self._index = faiss.IndexFlatL2(d)
        self._index.add(x)

        # range_search returns (lims, distances, indices)
        # threshold is squared L2 because IndexFlatL2 computes ||a-b||²
        lims, _D, indices = self._index.range_search(x, self.eps**2)

        # Convert FAISS compact output to per-point neighbour lists
        neighbors = [indices[lims[i] : lims[i + 1]].tolist() for i in range(n)]

        self._labels = self._label_clusters(neighbors, n, self.min_samples)
        return self

    def get_cluster_labels(self, x: "DashAIDataset | None" = None) -> np.ndarray:
        """Return cluster labels from the fitted model.

        DBSCAN does not support assigning labels to unseen samples (it is a
        non-parametric algorithm with no predict step). Passing a dataset with
        a different number of rows than the training set raises an error.

        Parameters
        ----------
        x : DashAIDataset, optional
            If provided, must have the same number of rows as the training set.

        Returns
        -------
        numpy.ndarray
            Cluster label per sample. Noise points are labelled ``-1``.
        """
        if self._labels is None:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before returning labels."
            )
        if x is not None and len(x) != len(self._labels):
            raise ValueError(
                f"{self.__class__.__name__} cannot assign labels to unseen samples."
            )
        return self._labels

    @staticmethod
    def _label_clusters(
        neighbors: list,
        n: int,
        min_samples: int,
    ) -> np.ndarray:
        """Apply DBSCAN cluster-labelling to precomputed neighbour lists.

        Core points are those with at least ``min_samples`` neighbours
        (including themselves). Clusters are grown via BFS from unvisited core
        points. Border points (non-core points reachable from a core point)
        receive the cluster label but do not expand. All remaining unvisited
        points are labelled -1 (noise).

        Parameters
        ----------
        neighbors : list of lists
            ``neighbors[i]`` contains the indices of all points within ``eps``
            of point ``i`` (including ``i`` itself).
        n : int
            Total number of samples.
        min_samples : int
            Minimum neighbourhood size for a point to be a core point.

        Returns
        -------
        numpy.ndarray of shape (n,), dtype int64
            Cluster label per sample. ``-1`` means noise.
        """
        is_core = np.array(
            [len(neighbors[i]) >= min_samples for i in range(n)], dtype=bool
        )
        labels = np.full(n, -1, dtype=np.int64)
        visited = np.zeros(n, dtype=bool)
        cluster_id = 0

        for point in range(n):
            if visited[point] or not is_core[point]:
                continue

            # Start a new cluster from this unvisited core point
            visited[point] = True
            labels[point] = cluster_id
            queue = list(neighbors[point])

            while queue:
                q = queue.pop(0)
                if visited[q]:
                    continue
                visited[q] = True
                labels[q] = cluster_id
                # Only core points expand the frontier
                if is_core[q]:
                    queue.extend(neighbors[q])

            cluster_id += 1

        return labels
