"""DashAI log loss implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class LogLoss(ClassificationMetric):
    """
    Negative log-likelihood of true labels under the predicted probability distribution.

    Log Loss (cross-entropy loss) penalises confident wrong predictions much
    more heavily than uncertain ones. Unlike accuracy or F1, it evaluates the
    full probability output of the classifier rather than just the argmax
    label, rewarding well-calibrated models.

    Lower values indicate better performance (``MAXIMIZE = False``). A perfect
    classifier achieves log loss of 0; a random classifier on a binary problem
    achieves approximately ln(2) ≈ 0.693.

    ::

        Log Loss = -(1/N) · Σᵢ Σ_c yᵢ_c · log(pᵢ_c)

    where yᵢ_c is 1 if sample i belongs to class c and pᵢ_c is the
    predicted probability.

    Range: [0, +∞), lower is better (``MAXIMIZE = False``).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Log Loss, also known as Logistic Loss or Cross-Entropy Loss, "
            "measures the performance of a classification model "
            "where the prediction input is a probability value "
            "between 0 and 1."
        ),
        es=(
            "Log Loss, también conocido como Pérdida Logística o Entropía Cruzada, "
            "mide el rendimiento de un modelo de clasificación "
            "donde la entrada de predicción es un valor de probabilidad "
            "entre 0 y 1."
        ),
        pt=(
            "Log Loss, também conhecido como Perda Logística ou Entropia Cruzada, "
            "mede o desempenho de um modelo de classificação "
            "onde a entrada de previsão é um valor de probabilidade "
            "entre 0 e 1."
        ),
        de=(
            "Log Loss, auch bekannt als Logistischer Verlust oder Kreuzentropieverlust,"
            "misst die Leistung eines Klassifikationsmodells, "
            "bei dem die Vorhersageeingabe ein Wahrscheinlichkeitswert "
            "zwischen 0 und 1 ist."
        ),
        zh=(
            "对数损失（也称为逻辑损失或交叉熵损失）衡量分类模型的性能，"
            "其中预测输入为 0 到 1 之间的概率值。"
        ),
    )

    MAXIMIZE: bool = False

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate Log Loss score between true labels and predicted labels.

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
            Log Loss, lower is better.
        """
        from sklearn.metrics import log_loss

        true_labels, _ = prepare_to_metric(true_labels, probs_pred_labels)
        # Pass all expected class indices so log_loss works even when a split
        # happens to contain only one class (e.g. small validation sets).
        n_classes = probs_pred_labels.shape[1]
        labels = list(range(n_classes))
        return log_loss(true_labels, probs_pred_labels, labels=labels)
