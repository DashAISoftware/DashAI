"""DashAI Cohen Kappa classification metric implementation."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class CohenKappa(ClassificationMetric):
    """Agreement between classifier predictions and true labels beyond chance.

    Cohen's Kappa (κ) measures the extent to which two raters (here, the model
    and ground truth) agree on class assignments, correcting for the probability
    of agreement occurring by chance. Unlike raw accuracy, Kappa accounts for
    class imbalance and is particularly useful when evaluating classifiers on
    unbalanced datasets.

    ::

        κ = (p_o - p_e) / (1 - p_e)

    where p_o is the observed agreement (accuracy) and p_e is the expected
    agreement by chance.

    Range: (-∞, 1]. Interpretation: < 0 worse than chance; 0.21-0.40 fair;
    0.41-0.60 moderate; 0.61-0.80 substantial; 0.81-1.0 almost perfect.

    References
    ----------
    - [1] Cohen, J. (1960). "A coefficient of agreement for nominal scales."
           Educational and Psychological Measurement, 20(1), 37-46.
    - [2] https://scikit-learn.org/stable/modules/generated/
           sklearn.metrics.cohen_kappa_score.html
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Cohen Kappa score measures the agreement between two raters "
            "who each classify items into mutually exclusive categories."
        ),
        es=(
            "El puntaje Cohen Kappa mide la concordancia entre dos evaluadores "
            "que clasifican elementos en categorías mutuamente excluyentes."
        ),
        pt=(
            "A pontuação Cohen Kappa mede a concordância entre dois avaliadores "
            "que classificam itens em categorias mutuamente exclusivas."
        ),
        de=(
            "Der Cohen-Kappa-Wert misst die Übereinstimmung zwischen zwei Bewertern, "
            "die jeweils Elemente in gegenseitig ausschließende Kategorien einteilen."
        ),
        zh="Cohen Kappa 分数衡量两位评分者将项目分配到相互排斥类别时的一致性程度。",
    )

    @staticmethod
    def score(
        true_labels: "DashAIDataset",
        probs_pred_labels: "np.ndarray",
        multiclass: Optional[bool] = None,
    ) -> float:
        """Calculate Cohen Kappa score between true labels and predicted labels.

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
            Cohen Kappa score between true labels and predicted labels
        """
        from sklearn.metrics import cohen_kappa_score

        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)

        return cohen_kappa_score(true_labels, pred_labels)
