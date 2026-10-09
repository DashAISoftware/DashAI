"""DashAI Matthews Correlation Coefficient classification metric implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MatthewsCorrCoef(ClassificationMetric):
    """Correlation between predicted and true labels, robust to class imbalance.

    The Matthews Correlation Coefficient (MCC) is a balanced measure of the
    quality of a classification that can be used even when the classes are of
    very different sizes. In essence it is the correlation coefficient between
    the observed and predicted classifications, computed from the confusion
    matrix.

    ::

        MCC = (TP·TN − FP·FN) /
              sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))

    Range: [-1, 1]. Interpretation: +1 a perfect prediction; 0 no better than
    random guessing; -1 total disagreement between prediction and observation.
    Because a high score requires the classifier to do well on every class
    (all four confusion-matrix quadrants), MCC is regarded as more informative
    than accuracy or F1 on imbalanced problems. It generalises to the
    multiclass setting via scikit-learn's implementation.

    References
    ----------
    - [1] Matthews, B.W. (1975). "Comparison of the predicted and observed
           secondary structure of T4 phage lysozyme." Biochimica et Biophysica
           Acta (BBA) - Protein Structure, 405(2), 442-451.
    - [2] Chicco, D. & Jurman, G. (2020). "The advantages of the Matthews
           correlation coefficient (MCC) over F1 score and accuracy in binary
           classification evaluation." BMC Genomics, 21(6).
    - [3] https://scikit-learn.org/stable/modules/generated/
           sklearn.metrics.matthews_corrcoef.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "The Matthews Correlation Coefficient measures the correlation "
            "between predicted and true labels, returning a value in [-1, 1] "
            "that stays reliable even when the classes are imbalanced."
        ),
        es=(
            "El Coeficiente de Correlación de Matthews mide la correlación "
            "entre las etiquetas predichas y verdaderas, devolviendo un valor "
            "en [-1, 1] que sigue siendo confiable incluso con clases "
            "desbalanceadas."
        ),
        pt=(
            "O Coeficiente de Correlação de Matthews mede a correlação entre "
            "os rótulos previstos e verdadeiros, retornando um valor em "
            "[-1, 1] que permanece confiável mesmo com classes desbalanceadas."
        ),
        de=(
            "Der Matthews-Korrelationskoeffizient misst die Korrelation "
            "zwischen vorhergesagten und wahren Labels und liefert einen Wert "
            "in [-1, 1], der auch bei unausgewogenen Klassen zuverlässig bleibt."
        ),
        zh="马修斯相关系数衡量预测标签与真实标签之间的相关性，返回 [-1, 1] "
        "范围内的值，即使在类别不平衡时也保持可靠。",
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate the Matthews Correlation Coefficient.

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
            Matthews Correlation Coefficient between true labels and predicted
            labels.
        """
        from sklearn.metrics import matthews_corrcoef

        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)

        return matthews_corrcoef(true_labels, pred_labels)
