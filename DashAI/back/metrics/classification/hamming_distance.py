"""DashAI Hamming Distance implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class HammingDistance(ClassificationMetric):
    """Fraction of labels that are incorrectly predicted (Hamming loss).

    The Hamming distance (or Hamming loss) is the fraction of the total
    predictions that are wrong. For single-label classification it equals
    ``1 - accuracy``; for multilabel classification it counts per-label
    mismatches independently, making it especially useful when each sample
    can belong to multiple classes simultaneously.

    A lower Hamming distance indicates better performance. ``MAXIMIZE = False``
    so the DashAI framework treats smaller values as improvements.

    ::

        Hamming Loss = (1/N) · Σᵢ 𝟙[ŷᵢ ≠ yᵢ]

    Range: [0, 1], lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] Hamming, R.W. (1950). "Error detecting and error correcting codes."
           Bell System Technical Journal, 29(2), 147-160.
    - [2] https://scikit-learn.org/stable/modules/generated/
           sklearn.metrics.hamming_loss.html
    """

    MAXIMIZE: bool = False
    DESCRIPTION = MultilingualString(
        en=(
            "Hamming Distance measures the fraction of "
            "labels that are incorrectly predicted. "
            "It is particularly useful for multilabel classification tasks."
        ),
        es=(
            "La Distancia de Hamming mide la fracción de "
            "etiquetas predichas incorrectamente. "
            "Es especialmente útil para tareas de clasificación multietiqueta."
        ),
        pt=(
            "A Distância de Hamming mede a fração de "
            "rótulos previstos incorretamente. "
            "É especialmente útil para tarefas de classificação multirrótulo."
        ),
        de=(
            "Die Hamming-Distanz misst den Anteil der "
            "falsch vorhergesagten Zielgrößen. "
            "Sie ist besonders nützlich für Multi-Label-Klassifikationsaufgaben."
        ),
        zh="汉明距离衡量预测错误的标签比例，特别适用于多标签分类任务。",
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate Hamming Distance between true labels and predicted labels.

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
            Hamming Distance between true labels and predicted labels
        """
        from sklearn.metrics import hamming_loss

        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        return hamming_loss(true_labels, pred_labels)
