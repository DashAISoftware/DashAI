"""Precision recall curve report."""

from typing import List, Optional

import numpy as np

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import (
    BaseReport,
    ReportError,
    resolve_class_names,
)
from DashAI.back.reports.classification.roc_curve import probability_matrix


class PrecisionRecallCurve(BaseReport):
    """One vs rest precision against recall, with average precision annotated.

    Preferred over ROC under class imbalance: the false positive rate that ROC
    plots is divided by the (large) number of true negatives, so a rare-positive
    problem can show an excellent ROC curve while the model is mostly wrong
    whenever it does predict the positive class. Precision has no such
    denominator, so this curve stays honest as the classes skew.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html
    """

    REQUIRES_PROBABILITIES: bool = True
    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="Precision Recall Curve",
        es="Curva Precisión-Exhaustividad",
        pt="Curva Precisão-Revocação",
        de="Precision-Recall-Kurve",
        zh="精确率召回率曲线",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Precision against recall per class; more honest than ROC when "
            "classes are imbalanced."
        ),
        es=(
            "Precisión contra exhaustividad por clase; más honesta que ROC "
            "cuando las clases están desbalanceadas."
        ),
        pt=(
            "Precisão contra revocação por classe; mais honesta que ROC quando "
            "as classes estão desbalanceadas."
        ),
        de=(
            "Genauigkeit gegen Trefferquote je Klasse; ehrlicher als ROC bei "
            "unausgeglichenen Klassen."
        ),
        zh="每个类别的精确率与召回率；在类别不平衡时比 ROC 更可靠。",
    )
    COLOR: str = "#AB47BC"
    ICON: str = "Timeline"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the one vs rest precision recall curves.

        Parameters
        ----------
        y_true : ndarray
            Encoded true class indexes.
        y_pred : ndarray
            Class probability matrix.
        class_names : Optional[List[str]]
            Class labels in encoded order.

        Returns
        -------
        List[Artifact]
            A single figure holding one curve per class.
        """
        import plotly.graph_objects as go
        from sklearn.metrics import average_precision_score, precision_recall_curve

        probabilities = probability_matrix(y_pred)
        truth = np.asarray(y_true).ravel()
        names = resolve_class_names(class_names, probabilities.shape[1])

        figure = go.Figure()
        target_classes = [1] if probabilities.shape[1] == 2 else range(len(names))
        for class_index in target_classes:
            positives = (truth == class_index).astype(int)
            if positives.sum() == 0 or positives.sum() == len(positives):
                continue
            precision, recall, _ = precision_recall_curve(
                positives, probabilities[:, class_index]
            )
            average = average_precision_score(positives, probabilities[:, class_index])
            figure.add_trace(
                go.Scatter(
                    x=recall.tolist(),
                    y=precision.tolist(),
                    mode="lines",
                    name=f"{names[class_index]} (AP {average:.3f})",
                    line={"width": 2},
                )
            )

        if not figure.data:
            raise ReportError(
                "The split holds a single class, so no precision recall curve "
                "is defined."
            )

        figure.update_layout(
            title="Precision recall curve (one vs rest)",
            xaxis_title="Recall",
            yaxis_title="Precision",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Precision recall curve")]
