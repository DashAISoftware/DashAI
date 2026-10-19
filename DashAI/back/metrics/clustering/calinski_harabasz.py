"""Calinski-Harabasz clustering metric."""

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


class CalinskiHarabasz(ClusteringMetric):
    """Ratio between inter-cluster and intra-cluster dispersion.

    Calinski-Harabasz evaluates how dense and well-separated clusters are by
    comparing dispersion between clusters with dispersion within clusters.
    Higher values generally indicate better-defined clusters.

    Range: [0, +inf), higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] Calinski, T. & Harabasz, J. (1974). "A dendrite method for cluster
           analysis." Communications in Statistics, 3(1), 1-27.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.calinski_harabasz_score.html
    """

    MAXIMIZE = True
    DESCRIPTION = MultilingualString(
        en="Higher values indicate dense and well-separated clusters.",
        es="Valores mayores indican clusters densos y bien separados.",
        pt="Valores mais altos indicam clusters densos e bem separados.",
        de="Höhere Werte deuten auf dichte und gut getrennte Cluster hin.",
        zh="值越高表示聚类越密集、分离度越好。",
    )

    @staticmethod
    def score(
        x: "DashAIDataset | pd.DataFrame",
        labels: "np.ndarray | list",
    ) -> float | None:
        """Calculate the Calinski-Harabasz score for clustering assignments.

        Parameters
        ----------
        x : DashAIDataset or pandas.DataFrame
            Feature data used by the clustering model.
        labels : np.ndarray or list
            Cluster labels assigned to each sample.

        Returns
        -------
        float | None
            Calinski-Harabasz score, or ``None`` when the score is not defined
            for the current label distribution.
        """
        from sklearn.metrics import calinski_harabasz_score

        x_values, label_values = prepare_to_metric(x, labels)
        if x_values is None:
            return None
        return float(calinski_harabasz_score(x_values, label_values))
