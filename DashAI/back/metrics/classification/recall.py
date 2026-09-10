"""DashAI recall classification metric implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class Recall(ClassificationMetric):
    """Fraction of actual positives that are correctly identified.

    Recall (also called sensitivity or true positive rate) measures the
    ability of the classifier to find all positive samples. It is the metric
    of choice when the cost of false negatives is high. For example, in
    medical screening, missing a disease is more costly than a false alarm.

    For binary tasks the standard binary recall is used. For multiclass tasks,
    macro averaging (unweighted mean over all classes) is applied.

    ::

        Recall = TP / (TP + FN)

    Range: [0, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Fraction of actual positives correctly identified, "
            "important when false negatives are costly."
        ),
        es=(
            "Fracción de positivos reales correctamente identificados, "
            "importante cuando los falsos negativos son costosos."
        ),
        pt=(
            "Fração dos positivos reais corretamente identificados, "
            "importante quando os falsos negativos são custosos."
        ),
        de=(
            "Anteil der tatsächlich positiven Fälle, die korrekt identifiziert wurden, "
            "wichtig wenn falsch-negative Ergebnisse kostspielig sind."
        ),
        zh=("实际正例中被正确识别的比例，在假阴性代价高昂时尤为重要。"),
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate recall between true labels and predicted labels.

        Parameters
        ----------
        true_labels : DashAIDataset
            A DashAI dataset with labels.
        probs_pred_labels : np.ndarray
            A two-dimensional matrix in which each column represents a class and the row
            values represent the probability that an example belongs to the class
            associated with the column.
        multiclass : bool, optional
            Whether the task is a multiclass classification. If None, it will be
            determined automatically from the number of unique labels.

        Returns
        -------
        float
            recall score between true labels and predicted labels
        """
        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)

        # Use the provided multiclass parameter or determine it from the number
        # of classes
        # Use probs_pred_labels.shape[1] (number of columns) for multiclass detection
        # because true_labels might be missing a class in a validation fold
        if multiclass is None:
            multiclass = probs_pred_labels.shape[1] > 2

        from sklearn.metrics import recall_score

        if multiclass:
            return recall_score(
                true_labels, pred_labels, average="macro", zero_division=0
            )
        else:
            return recall_score(
                true_labels, pred_labels, average="binary", zero_division=0
            )
