"""DashAI F1 clasification metric implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class F1(ClassificationMetric):
    """Harmonic mean of precision and recall.

    The F1 score balances precision (how many predicted positives are
    actually positive) and recall (how many actual positives were found).
    It is the preferred metric for imbalanced classification tasks where
    both false positives and false negatives carry equal cost.

    For binary tasks the standard F1 is used. For multiclass tasks, macro
    averaging (unweighted mean over all classes) is applied so that minority
    classes are not drowned out by majority classes.

    ::

        F1 = 2 · (Precision x Recall) / (Precision + Recall)

    Range: [0, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] Van Rijsbergen, C.J. (1979). *Information Retrieval* (2nd ed.).
           Butterworth-Heinemann.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Harmonic mean of precision and recall, "
            "useful for imbalanced classification tasks."
        ),
        es=(
            "Media armónica de precisión y exhaustividad, "
            "útil para tareas de clasificación desbalanceadas."
        ),
        pt=(
            "Média harmônica de precisão e revocação, "
            "útil para tarefas de classificação desbalanceadas."
        ),
        de=(
            "Harmonisches Mittel von Präzision und Trefferquote, "
            "nützlich für unausgewogene Klassifikationsaufgaben."
        ),
        zh=("精确率和召回率的调和平均值，对不均衡分类任务非常有用。"),
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate f1 score between true labels and predicted labels.

        Parameters
        ----------
        true_labels : DashAIDataset
            A DashAI dataset with labels.
        probs_pred_labels : np.ndarray
            A two-dimensional matrix in which each column represents a class
            and the row values represent the probability that an example belongs
            to the class associated with the column.
        multiclass : bool, optional
            Whether the task is a multiclass classification. If None, it will be
            determined automatically from the number of unique labels.

        Returns
        -------
        float
            f1 score between true labels and predicted labels
        """
        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        # Use the provided multiclass parameter or determine it from the number
        # of classes
        # Use probs_pred_labels.shape[1] (number of columns) for multiclass detection
        # because true_labels might be missing a class in a validation fold
        if multiclass is None:
            multiclass = probs_pred_labels.shape[1] > 2

        from sklearn.metrics import f1_score

        if multiclass:
            return f1_score(true_labels, pred_labels, average="macro", zero_division=0)
        else:
            return f1_score(true_labels, pred_labels, average="binary", zero_division=0)
