"""ROC curve report."""

from typing import List, Optional

import numpy as np

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import (
    BaseReport,
    ReportError,
    resolve_class_names,
)


def probability_matrix(y_pred) -> "np.ndarray":
    """Return the prediction as a probability matrix, or fail loudly.

    Parameters
    ----------
    y_pred : ndarray
        What the model's ``predict`` returned.

    Returns
    -------
    np.ndarray
        A ``(n_samples, n_classes)`` matrix.

    Raises
    ------
    ReportError
        If the model returned hard labels, which carry no ranking information
        and so cannot produce a curve.
    """
    predictions = np.asarray(y_pred, dtype=float)
    if predictions.ndim != 2 or predictions.shape[1] < 2:
        raise ReportError(
            "This report needs class probabilities, but the model returned "
            "hard labels. Pick a model that outputs probabilities."
        )
    return predictions


class RocCurve(BaseReport):
    """One vs rest ROC curve per class, with the AUC annotated.

    ROC AUC already exists as a metric because it is a single number. The curve
    is the shape that number condenses: it shows *where* along the operating
    range the model trades false positives for true positives, so two models
    with equal AUC can be told apart by which end of the range they are good at.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html
    """

    REQUIRES_PROBABILITIES: bool = True
    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="ROC Curve",
        es="Curva ROC",
        pt="Curva ROC",
        de="ROC-Kurve",
        zh="ROC 曲线",
    )
    DESCRIPTION: str = MultilingualString(
        en="True positive rate against false positive rate, one curve per class.",
        es=(
            "Tasa de verdaderos positivos contra falsos positivos, una curva por clase."
        ),
        pt=(
            "Taxa de verdadeiros positivos contra falsos positivos, uma curva "
            "por classe."
        ),
        de=("Richtig-Positiv-Rate gegen Falsch-Positiv-Rate, eine Kurve je Klasse."),
        zh="真正例率与假正例率的关系，每个类别一条曲线。",
    )
    COLOR: str = "#26A69A"
    ICON: str = "ShowChart"

    def __init__(self, **kwargs) -> None:
        """Initialise the report. It takes no parameters."""

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the one vs rest ROC curves.

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
            A single figure holding one curve per class plus the chance line.
        """
        import plotly.graph_objects as go
        from sklearn.metrics import auc, roc_curve

        probabilities = probability_matrix(y_pred)
        truth = np.asarray(y_true).ravel()
        names = resolve_class_names(class_names, probabilities.shape[1])

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode="lines",
                name="Chance",
                line={"dash": "dash", "width": 1, "color": "#9e9e9e"},
                hoverinfo="skip",
            )
        )

        # A binary problem is one curve, not two mirror images of each other.
        target_classes = [1] if probabilities.shape[1] == 2 else range(len(names))
        for class_index in target_classes:
            positives = (truth == class_index).astype(int)
            if positives.sum() == 0 or positives.sum() == len(positives):
                # Only one class present in this split: the curve is undefined.
                continue
            false_positive, true_positive, _ = roc_curve(
                positives, probabilities[:, class_index]
            )
            area = auc(false_positive, true_positive)
            figure.add_trace(
                go.Scatter(
                    x=false_positive.tolist(),
                    y=true_positive.tolist(),
                    mode="lines",
                    name=f"{names[class_index]} (AUC {area:.3f})",
                    line={"width": 2},
                )
            )

        if len(figure.data) == 1:
            raise ReportError(
                "The split holds a single class, so no ROC curve is defined."
            )

        figure.update_layout(
            title="ROC curve (one vs rest)",
            xaxis_title="False positive rate",
            yaxis_title="True positive rate",
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="ROC curve")]
