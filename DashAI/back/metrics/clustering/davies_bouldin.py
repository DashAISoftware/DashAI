"""Davies-Bouldin clustering metric."""

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


class DaviesBouldin(ClusteringMetric):
    """Average similarity between each cluster and its closest cluster.

    Davies-Bouldin compares within-cluster dispersion with separation between
    clusters. Lower values indicate that clusters are compact and far from one
    another. A value of 0 is ideal, though uncommon in real datasets.

    Range: [0, +inf), lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] Davies, D. L. & Bouldin, D. W. (1979). "A Cluster Separation
           Measure." IEEE Transactions on Pattern Analysis and Machine
           Intelligence, PAMI-1(2), 224-227.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.davies_bouldin_score.html
    """

    MAXIMIZE = False
    DESCRIPTION = MultilingualString(
        en="Lower values indicate clusters that are more compact and separated.",
        es="Valores menores indican clusters mas compactos y separados.",
        pt="Valores mais baixos indicam clusters mais compactos e separados.",
        de="Niedrigere Werte deuten auf kompaktere und besser getrennte Cluster hin.",
        zh="值越低表示聚类越紧密、分离度越好。",
    )

    @staticmethod
    def score(
        x: "DashAIDataset | pd.DataFrame",
        labels: "np.ndarray | list",
    ) -> float | None:
        """Calculate the Davies-Bouldin score for clustering assignments.

        Parameters
        ----------
        x : DashAIDataset or pandas.DataFrame
            Feature data used by the clustering model.
        labels : np.ndarray or list
            Cluster labels assigned to each sample.

        Returns
        -------
        float | None
            Davies-Bouldin score, or ``None`` when the score is not defined for
            the current label distribution.
        """
        from sklearn.metrics import davies_bouldin_score

        x_values, label_values = prepare_to_metric(x, labels)
        if x_values is None:
            return None
        return float(davies_bouldin_score(x_values, label_values))
