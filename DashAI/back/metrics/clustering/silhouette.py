"""Silhouette clustering metric."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.clustering_metric import (
    ClusteringMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class Silhouette(ClusteringMetric):
    """Mean Silhouette Coefficient over all clustered samples.

    Silhouette measures how similar each sample is to samples in its own
    cluster compared with samples in the nearest different cluster. Values
    close to 1 indicate compact and well-separated clusters, values near 0
    indicate overlapping clusters, and negative values suggest that samples
    may have been assigned to the wrong cluster.

    Range: [-1, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] Rousseeuw, P. J. (1987). "Silhouettes: A graphical aid to the
           interpretation and validation of cluster analysis." Journal of
           Computational and Applied Mathematics, 20, 53-65.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html
    """

    MAXIMIZE = True
    DESCRIPTION = MultilingualString(
        en="Measures how well samples fit within their assigned clusters.",
        es="Mide que tan bien las muestras calzan dentro de sus clusters asignados.",
        pt="Mede o quão bem as amostras se encaixam em seus clusters atribuídos.",
        de="Misst, wie gut die Stichproben in ihre zugewiesenen Cluster passen.",
        zh="衡量样本与其所分配聚类的契合程度。",
    )

    @staticmethod
    def score(
        x: "DashAIDataset | pd.DataFrame",
        labels: "np.ndarray | list",
    ) -> float | None:
        """Calculate the Silhouette score for clustering assignments.

        Parameters
        ----------
        x : DashAIDataset or pandas.DataFrame
            Feature data used by the clustering model.
        labels : np.ndarray or list
            Cluster labels assigned to each sample.

        Returns
        -------
        float | None
            Silhouette score, or ``None`` when the score is not defined for the
            current label distribution.
        """
        from sklearn.metrics import silhouette_score

        x_values, label_values = prepare_to_metric(x, labels)
        if x_values is None:
            return None
        return float(silhouette_score(x_values, label_values))
