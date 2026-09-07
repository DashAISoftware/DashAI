from typing import List, Optional, Union

from DashAI.back.core.artifacts import (
    Artifact,
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class RegressionPartialDependenceSchema(BaseSchema):
    """Schema for the regression Partial Dependence explainer.

    Configures the grid resolution and the percentile range of each
    feature's grid.
    """

    grid_resolution: schema_field(
        int_field(ge=5, le=200),
        placeholder=50,
        description=MultilingualString(
            en="Number of equally spaced grid points per feature.",
            es="Número de puntos de la grilla equiespaciados por característica.",
            pt="Número de pontos de grade igualmente espaçados por característica.",
            zh="每个特征等距网格点的数量。",
            de="Anzahl gleichmäßig verteilter Gitterpunkte pro Merkmal.",
        ),
        alias=MultilingualString(
            en="Grid resolution",
            es="Resolución de la grilla",
            pt="Resolução da grade",
            zh="网格分辨率",
            de="Gitterauflösung",
        ),
    )  # type: ignore

    lower_percentile: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.05,
        description=MultilingualString(
            en="Lower percentile of the feature values used as grid start.",
            es="Percentil inferior de los valores usados como inicio de la grilla.",
            pt="Percentil inferior dos valores usados como início da grade.",
            zh="用作网格起点的特征值下分位数。",
            de="Unteres Perzentil der Merkmalswerte als Gitterstart.",
        ),
        alias=MultilingualString(
            en="Lower percentile",
            es="Percentil inferior",
            pt="Percentil inferior",
            zh="下分位数",
            de="Unteres Perzentil",
        ),
    )  # type: ignore

    upper_percentile: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.95,
        description=MultilingualString(
            en="Upper percentile of the feature values used as grid end.",
            es="Percentil superior de los valores usados como fin de la grilla.",
            pt="Percentil superior dos valores usados como fim da grade.",
            zh="用作网格终点的特征值上分位数。",
            de="Oberes Perzentil der Merkmalswerte als Gitterende.",
        ),
        alias=MultilingualString(
            en="Upper percentile",
            es="Percentil superior",
            pt="Percentil superior",
            zh="上分位数",
            de="Oberes Perzentil",
        ),
    )  # type: ignore


class RegressionPartialDependence(BaseGlobalExplainer):
    """Partial dependence curves for regression models.

    For each numeric feature, sweeps a grid of values, replaces the feature
    with each grid value across the test set and averages the model's
    predictions, showing the marginal effect of the feature on the predicted
    value. Model agnostic (only ``predict`` is queried); assumes features are
    not strongly correlated.

    References
    ----------
    - [1] Friedman, J.H. (2001). "Greedy Function Approximation: A Gradient
           Boosting Machine." Annals of Statistics 29(5).
    - [2] https://scikit-learn.org/stable/modules/partial_dependence.html
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME = MultilingualString(
        en="Partial Dependence (regression)",
        es="Dependencia Parcial (regresión)",
        pt="Dependência Parcial (regressão)",
        zh="部分依赖（回归）",
        de="Partielle Abhängigkeit (Regression)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Shows how the model's predicted value changes on average as each "
            "feature sweeps through its range."
        ),
        es=(
            "Muestra cómo cambia en promedio el valor predicho por el modelo "
            "a medida que cada característica recorre su rango."
        ),
        pt=(
            "Mostra como o valor previsto pelo modelo muda em média à medida "
            "que cada característica percorre seu intervalo."
        ),
        zh="展示随着每个特征遍历其取值范围，模型预测值的平均变化。",
        de=(
            "Zeigt, wie sich der vorhergesagte Wert des Modells im Mittel "
            "ändert, wenn jedes Merkmal seinen Wertebereich durchläuft."
        ),
    )
    COLOR = "#5D4037"
    SCHEMA = RegressionPartialDependenceSchema

    def __init__(
        self,
        model: BaseModel,
        grid_resolution: int = 50,
        lower_percentile: float = 0.05,
        upper_percentile: float = 0.95,
    ):
        """Initialise the regression Partial Dependence explainer.

        Parameters
        ----------
        model : BaseModel
            The trained DashAI regression model to be explained.
        grid_resolution : int
            Number of grid points per feature.
        lower_percentile : float
            Lower percentile of the feature values used as grid start.
        upper_percentile : float
            Upper percentile of the feature values used as grid end.
        """
        super().__init__(model)
        assert lower_percentile < upper_percentile, (
            "lower_percentile must be smaller than upper_percentile"
        )
        self.grid_resolution = grid_resolution
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile

    def explain(self, dataset):
        """Compute partial dependence curves on the test split.

        Parameters
        ----------
        dataset : Tuple[DatasetDict, DatasetDict]
            A ``(x, y)`` pair where each element has at least a ``"test"``
            split.

        Returns
        -------
        dict
            Mapping from feature name to ``{"grid_values", "average"}``,
            plus a ``"metadata"`` entry with the output column name.
        """
        import numpy as np

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = dataset
        # The grid frames are already in the model feature space, so the model
        # is queried through predict_prepared to skip a second preparation.
        x_test = prepare_model_input(self.model, x["test"]).to_pandas()

        # Cap rows to bound the number of model evaluations.
        max_rows = 200
        if len(x_test) > max_rows:
            x_test = x_test.iloc[:max_rows]

        output_column = y["test"].column_names[0]
        explanation = {"metadata": {"output_column": output_column}}

        for column in x_test.columns:
            if not np.issubdtype(x_test[column].dtype, np.number):
                continue

            values = x_test[column].to_numpy(dtype=float)
            start = np.quantile(values, self.lower_percentile)
            stop = np.quantile(values, self.upper_percentile)
            grid = np.linspace(start, stop, self.grid_resolution)

            averages = []
            frame = x_test.copy()
            for grid_value in grid:
                frame[column] = grid_value
                predictions = np.asarray(self.model.predict_prepared(frame)).ravel()
                averages.append(float(np.round(np.mean(predictions), 4)))

            explanation[column] = {
                "grid_values": np.round(grid, 4).tolist(),
                "average": averages,
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Create a grouped artifact with one line plot group per feature.

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact whose groups are one plotly curve per
            numeric feature.
        """
        import plotly.graph_objs as go

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        output_column = metadata["output_column"]

        groups = []
        for feature, curve in exp.items():
            fig = go.Figure(
                go.Scatter(
                    x=curve["grid_values"],
                    y=curve["average"],
                    mode="lines",
                )
            )
            fig.update_layout(
                title={
                    "text": f"Partial dependence of {output_column} on {feature}",
                    "font": {"size": 14},
                },
                xaxis={"title_text": feature},
                yaxis={"title_text": f"Average predicted {output_column}"},
                margin={"l": 60, "r": 30, "t": 50, "b": 50},
            )
            groups.append(
                ArtifactGroup(title=feature, artifacts=[PlotlyArtifact(payload=fig)])
            )

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: Union[Artifact, ArtifactGroup]
    ) -> Optional[MultilingualString]:
        """Describe, in words, the trend of one feature's dependence curve.

        Classifies the curve as increasing, decreasing or non-monotonic from
        its values (the same ones plotted by :meth:`plot`), and reports the
        predicted-value range across the feature's grid.

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.
        explainer_output : Union[Artifact, ArtifactGroup]
            One of the groups previously returned by :meth:`plot`, titled
            with the feature name.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised feature group.
        """
        if not isinstance(explainer_output, ArtifactGroup):
            return None
        feature = explainer_output.title
        if feature is None or feature not in explanation:
            return None

        output_column = explanation["metadata"]["output_column"]
        curve = explanation[feature]
        values = curve["average"]
        grid_values = curve["grid_values"]

        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        if max(values) - min(values) <= 1e-9:
            trend = "flat"
        elif all(d >= -1e-9 for d in diffs):
            trend = "increases"
        elif all(d <= 1e-9 for d in diffs):
            trend = "decreases"
        else:
            trend = "non_monotonic"

        start_value, end_value = grid_values[0], grid_values[-1]

        if trend == "flat":
            return format_story(
                {
                    "en": (
                        "Changing {feature} from {start_value} to {end_value} "
                        "does not noticeably affect the predicted "
                        "{output_column}, which stays at {start_pred}."
                    ),
                    "es": (
                        "Cambiar {feature} de {start_value} a {end_value} no "
                        "afecta de forma apreciable el {output_column} "
                        "predicho, que se mantiene en {start_pred}."
                    ),
                    "pt": (
                        "Alterar {feature} de {start_value} para {end_value} "
                        "não afeta de forma perceptível o {output_column} "
                        "previsto, que permanece em {start_pred}."
                    ),
                    "de": (
                        "Eine Änderung von {feature} von {start_value} auf "
                        "{end_value} wirkt sich nicht merklich auf den "
                        "vorhergesagten {output_column} aus, der bei "
                        "{start_pred} bleibt."
                    ),
                    "zh": (
                        "将{feature}从{start_value}变化到{end_value}对"
                        "预测的{output_column}没有明显影响，其保持在"
                        "{start_pred}。"
                    ),
                },
                feature=feature,
                output_column=output_column,
                start_value=start_value,
                end_value=end_value,
                start_pred=values[0],
            )

        if trend == "increases":
            return format_story(
                {
                    "en": (
                        "As {feature} goes from {start_value} to {end_value}, "
                        "the predicted {output_column} increases from "
                        "{start_pred} to {end_pred}."
                    ),
                    "es": (
                        "A medida que {feature} va de {start_value} a "
                        "{end_value}, el {output_column} predicho aumenta de "
                        "{start_pred} a {end_pred}."
                    ),
                    "pt": (
                        "À medida que {feature} vai de {start_value} a "
                        "{end_value}, o {output_column} previsto aumenta de "
                        "{start_pred} para {end_pred}."
                    ),
                    "de": (
                        "Während {feature} von {start_value} auf {end_value} "
                        "steigt, nimmt der vorhergesagte {output_column} von "
                        "{start_pred} auf {end_pred} zu."
                    ),
                    "zh": (
                        "随着{feature}从{start_value}变化到{end_value}，"
                        "预测的{output_column}从{start_pred}上升到"
                        "{end_pred}。"
                    ),
                },
                feature=feature,
                output_column=output_column,
                start_value=start_value,
                end_value=end_value,
                start_pred=values[0],
                end_pred=values[-1],
            )

        if trend == "decreases":
            return format_story(
                {
                    "en": (
                        "As {feature} goes from {start_value} to {end_value}, "
                        "the predicted {output_column} decreases from "
                        "{start_pred} to {end_pred}."
                    ),
                    "es": (
                        "A medida que {feature} va de {start_value} a "
                        "{end_value}, el {output_column} predicho disminuye "
                        "de {start_pred} a {end_pred}."
                    ),
                    "pt": (
                        "À medida que {feature} vai de {start_value} a "
                        "{end_value}, o {output_column} previsto diminui de "
                        "{start_pred} para {end_pred}."
                    ),
                    "de": (
                        "Während {feature} von {start_value} auf {end_value} "
                        "steigt, sinkt der vorhergesagte {output_column} von "
                        "{start_pred} auf {end_pred}."
                    ),
                    "zh": (
                        "随着{feature}从{start_value}变化到{end_value}，"
                        "预测的{output_column}从{start_pred}下降到"
                        "{end_pred}。"
                    ),
                },
                feature=feature,
                output_column=output_column,
                start_value=start_value,
                end_value=end_value,
                start_pred=values[0],
                end_pred=values[-1],
            )

        return format_story(
            {
                "en": (
                    "As {feature} goes from {start_value} to {end_value}, "
                    "the predicted {output_column} does not change "
                    "monotonically, ranging between {min_pred} and "
                    "{max_pred}."
                ),
                "es": (
                    "A medida que {feature} va de {start_value} a "
                    "{end_value}, el {output_column} predicho no cambia de "
                    "forma monótona, variando entre {min_pred} y "
                    "{max_pred}."
                ),
                "pt": (
                    "À medida que {feature} vai de {start_value} a "
                    "{end_value}, o {output_column} previsto não muda de "
                    "forma monótona, variando entre {min_pred} e "
                    "{max_pred}."
                ),
                "de": (
                    "Während {feature} von {start_value} auf {end_value} "
                    "steigt, ändert sich der vorhergesagte {output_column} "
                    "nicht monoton und schwankt zwischen {min_pred} und "
                    "{max_pred}."
                ),
                "zh": (
                    "随着{feature}从{start_value}变化到{end_value}，"
                    "预测的{output_column}并非单调变化，在{min_pred}和"
                    "{max_pred}之间波动。"
                ),
            },
            feature=feature,
            output_column=output_column,
            start_value=start_value,
            end_value=end_value,
            min_pred=min(values),
            max_pred=max(values),
        )
