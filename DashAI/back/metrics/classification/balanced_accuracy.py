"""DashAI balanced accuracy classification metric implementation."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BalancedAccuracy(ClassificationMetric):
    """Average of recall obtained on each class.

    Balanced Accuracy is the macro-average of recall scores per class. It
    avoids the inflated performance estimates that plain accuracy gives on
    imbalanced datasets, since each class contributes equally regardless of
    how many samples it has.

    ::

        Balanced Accuracy = (1 / C) * sum(recall_c for c in classes)

    Range: [0, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html
    """

    DESCRIPTION = MultilingualString(
        en=("Macro-average of recall per class, best suited for imbalanced datasets."),
        es=(
            "Promedio macro del recall por clase, más adecuado para "
            "datasets desbalanceados."
        ),
        pt=(
            "Média macro do recall por classe, mais adequada para "
            "conjuntos de dados desbalanceados."
        ),
        de=(
            "Makro-Durchschnitt des Recalls je Klasse, am besten geeignet für "
            "unausgewogene Datensätze."
        ),
        zh=("按类别宏平均的召回率，最适用于类别不均衡的数据集。"),
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
    ) -> float:
        """Calculate the balanced accuracy between true and predicted labels.

        Parameters
        ----------
        true_labels : DashAIDataset
            A DashAI dataset with labels.
        probs_pred_labels : np.ndarray
            A two-dimensional matrix in which each column represents a class
            and the row values represent the probability that an example belongs
            to the class associated with the column.

        Returns
        -------
        float
            Balanced accuracy score between true labels and predicted labels
        """
        from sklearn.metrics import balanced_accuracy_score

        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        return balanced_accuracy_score(true_labels, pred_labels)
