"""Per class precision, recall, F1 and support as a table."""

from typing import List, Optional

from DashAI.back.core.artifacts import (
    Artifact,
    TableArtifact,
    TablePayload,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import (
    BaseReport,
    as_labels,
    resolve_class_names,
)


class PerClassBreakdown(BaseReport):
    """Precision, recall, F1 and support broken down per class.

    The aggregate precision and recall metrics average over classes and so hide
    the case that matters most: a model that scores well overall while being
    useless on a small class. This table is that breakdown, with support
    included so a weak row can be read against how many samples back it.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.per_class_breakdown.html
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="Per Class Breakdown",
        es="Desglose por Clase",
        pt="Detalhamento por Classe",
        de="Aufschlüsselung je Klasse",
        zh="分类别明细",
    )
    DESCRIPTION: str = MultilingualString(
        en="Precision, recall, F1 and support for every class.",
        es="Precisión, exhaustividad, F1 y soporte para cada clase.",
        pt="Precisão, revocação, F1 e suporte para cada classe.",
        de="Genauigkeit, Trefferquote, F1 und Support für jede Klasse.",
        zh="每个类别的精确率、召回率、F1 和支持度。",
    )
    COLOR: str = "#66BB6A"
    ICON: str = "TableChart"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the per class report table.

        Parameters
        ----------
        y_true : ndarray
            Encoded true class indexes.
        y_pred : ndarray
            Model predictions, probabilities or hard labels.
        class_names : Optional[List[str]]
            Class labels in encoded order.

        Returns
        -------
        List[Artifact]
            A single table artifact, one row per class plus the averages.
        """
        import numpy as np
        from sklearn.metrics import precision_recall_fscore_support

        labels = as_labels(y_pred)
        truth = np.asarray(y_true).ravel()
        n_classes = int(max(truth.max(), labels.max())) + 1
        names = resolve_class_names(class_names, n_classes)
        indexes = list(range(n_classes))

        precision, recall, f1, support = precision_recall_fscore_support(
            truth, labels, labels=indexes, zero_division=0
        )

        rows = [
            [
                names[index],
                round(float(precision[index]), 4),
                round(float(recall[index]), 4),
                round(float(f1[index]), 4),
                int(support[index]),
            ]
            for index in indexes
        ]

        for average in ("macro", "weighted"):
            avg_precision, avg_recall, avg_f1, _ = precision_recall_fscore_support(
                truth, labels, labels=indexes, average=average, zero_division=0
            )
            rows.append(
                [
                    f"{average} avg",
                    round(float(avg_precision), 4),
                    round(float(avg_recall), 4),
                    round(float(avg_f1), 4),
                    int(support.sum()),
                ]
            )

        return [
            TableArtifact(
                payload=TablePayload(
                    columns=["Class", "Precision", "Recall", "F1", "Support"],
                    rows=rows,
                ),
                title="Per class breakdown",
            )
        ]
