"""DashAI RoC AUC classification metric implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ROCAUC(ClassificationMetric):
    """Area under the Receiver Operating Characteristic curve.

    ROC AUC measures the classifier's ability to distinguish between classes
    across all possible decision thresholds. The ROC curve plots the true
    positive rate (recall) against the false positive rate, and the AUC
    summarises the entire curve in a single scalar. A value of 0.5 indicates
    no discriminative ability (random classifier); 1.0 is a perfect classifier.

    For binary tasks, the probability of the positive class (column index 1)
    is used. For multiclass tasks, a one-vs-rest (OvR) averaging strategy is
    applied so that each class is treated as a binary problem in turn.

    Unlike accuracy-based metrics, ROC AUC uses the raw probability outputs
    from the model rather than hard class predictions, making it sensitive to
    model calibration.

    Range: [0, 1], higher is better (``MAXIMIZE = True``).

    References
    ----------
    - [1] Fawcett, T. (2006). "An introduction to ROC analysis."
           Pattern Recognition Letters, 27(8), 861-874.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "The Receiver Operating Characteristic Area Under the Curve (RoC AUC) "
            "is a performance measurement for classification problems at various "
            "threshold settings. It represents the degree or measure "
            "of separability between classes."
        ),
        es=(
            "El Área Bajo la Curva ROC (RoC AUC) "
            "es una medida de rendimiento para problemas de clasificación en varios "
            "umbrales de decisión. Representa el grado de "
            "separabilidad entre clases."
        ),
        pt=(
            "A Área Sob a Curva ROC (RoC AUC) "
            "é uma medida de desempenho para problemas de classificação "
            "em vários limiares de decisão. Representa o grau de "
            "separabilidade entre classes."
        ),
        de=(
            "Die Fläche unter der ROC-Kurve (RoC AUC) "
            "ist ein Leistungsmaß für Klassifikationsprobleme bei verschiedenen "
            "Schwellenwert-Einstellungen. Sie repräsentiert den Grad der "
            "Trennbarkeit zwischen Klassen."
        ),
        zh=(
            "ROC 曲线下面积（ROC AUC）是在不同阈值设置下衡量分类问题性能的指标，"
            "代表类别间的可分离程度。"
        ),
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate RoC AUC score between true labels and predicted labels.

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
            RoC AUC score between true labels and predicted labels
        """
        import numpy as np

        true_labels, _ = prepare_to_metric(true_labels, probs_pred_labels)

        # ROC AUC is undefined when only one class is present in y_true.
        if len(np.unique(true_labels)) < 2:
            return float("nan")

        from sklearn.metrics import roc_auc_score

        n_classes = probs_pred_labels.shape[1]

        if multiclass is None:
            multiclass = n_classes > 2
        try:
            if multiclass:
                return roc_auc_score(
                    true_labels,
                    probs_pred_labels,
                    multi_class="ovr",
                    labels=list(range(n_classes)),
                )
            else:
                return roc_auc_score(true_labels, probs_pred_labels[:, 1])
        except ValueError:
            return float("nan")
