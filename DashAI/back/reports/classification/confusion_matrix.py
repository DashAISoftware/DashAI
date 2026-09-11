"""Confusion matrix report."""

from typing import List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import BaseSchema, enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.reports.base_report import (
    BaseReport,
    as_labels,
    resolve_class_names,
)


class ConfusionMatrixSchema(BaseSchema):
    """Schema that configures the confusion matrix."""

    normalize: schema_field(
        enum_field(enum=["none", "true", "pred"]),
        placeholder="none",
        description=MultilingualString(
            en=(
                "How to normalise the counts. 'none' shows raw counts, 'true' "
                "divides each row by its true class total (recall per class), "
                "'pred' divides each column by its predicted total (precision "
                "per class)."
            ),
            es=(
                "Cómo normalizar los conteos. 'none' muestra conteos crudos, "
                "'true' divide cada fila por el total de su clase real "
                "(exhaustividad por clase), 'pred' divide cada columna por su "
                "total predicho (precisión por clase)."
            ),
            pt=(
                "Como normalizar as contagens. 'none' mostra contagens brutas, "
                "'true' divide cada linha pelo total da sua classe real "
                "(revocação por classe), 'pred' divide cada coluna pelo seu "
                "total previsto (precisão por classe)."
            ),
            de=(
                "Wie die Zählungen normalisiert werden. 'none' zeigt Rohwerte, "
                "'true' teilt jede Zeile durch die Gesamtzahl ihrer echten "
                "Klasse (Trefferquote je Klasse), 'pred' teilt jede Spalte "
                "durch ihre vorhergesagte Gesamtzahl (Genauigkeit je Klasse)."
            ),
            zh=(
                "如何归一化计数。'none' 显示原始计数，'true' 将每行除以其真实"
                "类别总数（每类召回率），'pred' 将每列除以其预测总数"
                "（每类精确率）。"
            ),
        ),
        alias=MultilingualString(
            en="Normalize",
            es="Normalizar",
            pt="Normalizar",
            de="Normalisieren",
            zh="归一化",
        ),
    )  # type: ignore


class ConfusionMatrix(BaseReport):
    """K x K grid of true class against predicted class.

    Reading the grid tells you *which* classes a model confuses, which the
    scalar accuracy summarising it cannot: two models with identical accuracy
    can fail in completely different places. Off diagonal mass concentrated in
    one cell means a systematic confusion between that pair of classes; mass
    spread evenly across a row means the model has no signal for that class.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html
    """

    SCHEMA = ConfusionMatrixSchema
    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="Confusion Matrix",
        es="Matriz de Confusión",
        pt="Matriz de Confusão",
        de="Konfusionsmatrix",
        zh="混淆矩阵",
    )
    DESCRIPTION: str = MultilingualString(
        en="Which classes the model confuses, as a true against predicted grid.",
        es=("Qué clases confunde el modelo, como una grilla de real contra predicho."),
        pt=("Quais classes o modelo confunde, como uma grade de real contra previsto."),
        de=(
            "Welche Klassen das Modell verwechselt, als Gitter aus echt gegen "
            "vorhergesagt."
        ),
        zh="模型混淆了哪些类别，以真实类别与预测类别的网格呈现。",
    )
    COLOR: str = "#5C6BC0"
    ICON: str = "GridOn"

    def __init__(self, normalize: str = "none", **kwargs) -> None:
        """Initialise the report.

        Parameters
        ----------
        normalize : str
            One of ``"none"``, ``"true"`` or ``"pred"``.
        **kwargs : dict
            Ignored; accepted so unknown stored parameters do not break loading.
        """
        self.normalize = normalize

    def compute(
        self,
        y_true,
        y_pred,
        class_names: Optional[List[str]] = None,
    ) -> List[Artifact]:
        """Build the confusion matrix heatmap.

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
            A single heatmap artifact.
        """
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.metrics import confusion_matrix

        labels = as_labels(y_pred)
        truth = np.asarray(y_true).ravel()
        n_classes = int(max(truth.max(), labels.max())) + 1
        names = resolve_class_names(class_names, n_classes)

        matrix = confusion_matrix(truth, labels, labels=list(range(n_classes))).astype(
            float
        )

        if self.normalize == "true":
            totals = matrix.sum(axis=1, keepdims=True)
            title_suffix = " (row normalized)"
        elif self.normalize == "pred":
            totals = matrix.sum(axis=0, keepdims=True)
            title_suffix = " (column normalized)"
        else:
            totals = None
            title_suffix = ""

        if totals is not None:
            # An unpredicted class leaves a zero total; leave those cells at 0
            # rather than emitting NaN, which plotly renders as a hole.
            with np.errstate(divide="ignore", invalid="ignore"):
                matrix = np.divide(
                    matrix, totals, out=np.zeros_like(matrix), where=totals != 0
                )

        text_format = "{:.0f}" if totals is None else "{:.2f}"
        figure = go.Figure(
            go.Heatmap(
                z=matrix.tolist(),
                x=names,
                y=names,
                colorscale="Blues",
                text=[[text_format.format(value) for value in row] for row in matrix],
                texttemplate="%{text}",
                hovertemplate=(
                    "true: %{y}<br>predicted: %{x}<br>value: %{z}<extra></extra>"
                ),
            )
        )
        figure.update_layout(
            title=f"Confusion matrix{title_suffix}",
            xaxis_title="Predicted",
            yaxis_title="True",
            # Read top-left to bottom-right like the printed convention.
            yaxis={"autorange": "reversed"},
            margin={"l": 20, "r": 20, "t": 50, "b": 40},
        )
        return [PlotlyArtifact(payload=figure, title="Confusion matrix")]
