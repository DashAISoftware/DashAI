import re
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
from DashAI.back.types.categorical import Categorical


class PartialDependenceSchema(BaseSchema):
    """Schema for PartialDependence explainer hyperparameters.

    Configures the grid resolution (number of evenly-spaced evaluation points per
    feature) and the fraction of training samples used to compute the marginal
    averages. Higher grid resolution gives smoother curves at the cost of more
    model evaluations.
    """

    grid_resolution: schema_field(
        int_field(ge=1),
        placeholder=100,
        description=MultilingualString(
            en=(
                "Number of equidistant points to split the range of the target feature."
            ),
            es=(
                "Número de puntos equidistantes para dividir el rango de la "
                "característica objetivo."
            ),
            pt=(
                "Número de pontos equidistantes para dividir o intervalo da "
                "característica alvo."
            ),
            de=(
                "Anzahl der äquidistanten Punkte zur Aufteilung des Wertebereichs "
                "des Zielmerkmals."
            ),
            zh="将目标特征范围分割为等距点的数量。",
        ),
        alias=MultilingualString(
            en="Grid resolution",
            es="Resolución de la malla",
            pt="Resolução da grade",
            de="Rasterauflösung",
            zh="网格分辨率",
        ),
    )  # type: ignore

    lower_percentile: schema_field(
        float_field(ge=0, le=0.99),
        placeholder=0.05,
        description=MultilingualString(
            en=("Lower percentile used to limit the feature values."),
            es=("Percentil inferior para limitar los valores de la característica."),
            pt=("Percentil inferior para limitar os valores da característica."),
            de=("Unteres Perzentil zur Begrenzung der Merkmalswerte."),
            zh="用于限制特征值的下百分位数。",
        ),
        alias=MultilingualString(
            en="Lower percentile",
            es="Percentil inferior",
            pt="Percentil inferior",
            de="Unteres Perzentil",
            zh="下百分位数",
        ),
    )  # type: ignore

    upper_percentile: schema_field(
        float_field(ge=0.01, le=1),
        placeholder=0.95,
        description=MultilingualString(
            en=("Upper percentile used to limit the feature values."),
            es=("Percentil superior para limitar los valores de la característica."),
            pt=("Percentil superior para limitar os valores da característica."),
            de=("Oberes Perzentil zur Begrenzung der Merkmalswerte."),
            zh="用于限制特征值的上百分位数。",
        ),
        alias=MultilingualString(
            en="Upper percentile",
            es="Percentil superior",
            pt="Percentil superior",
            de="Oberes Perzentil",
            zh="上百分位数",
        ),
    )  # type: ignore


class PartialDependence(BaseGlobalExplainer):
    """Global explainer that shows how the model's average prediction
    changes with each feature.

    A Partial Dependence Plot (PDP) marginalises the model output over the
    distribution of all other features, leaving a curve (or surface) that
    shows the average effect of the target feature in isolation. For a feature
    `x_j`, the partial dependence is:

    ::

        f̄(x_j) = E_(x_-j) [ f(x_j, x_-j) ] ≈ (1/n) Σ_i f(x_j, x_-j,i)


    PDPs assume feature independence; when features are correlated, the
    marginalisation extrapolates into regions with low data density. Individual
    Conditional Expectation (ICE) plots (one line per sample) can be overlaid
    to detect heterogeneous effects hidden by the average.

    References
    ----------
    - [1] Friedman, J.H. (2001). "Greedy function approximation: A gradient
           boosting machine." Annals of Statistics, 29(5), 1189-1232.
    - [2] https://scikit-learn.org/stable/modules/partial_dependence.html
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Partial Dependence",
        es="Dependencia Parcial",
        pt="Dependência Parcial",
        de="Partielle Abhängigkeit",
        zh="部分依赖",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Partial Dependence shows the marginal effect of a feature on the "
            "model's predicted probability by averaging over the distribution of "
            "other features."
        ),
        es=(
            "La Dependencia Parcial muestra el efecto marginal de una "
            "característica sobre la probabilidad predicha por el modelo, "
            "promediando sobre la distribución del resto de características."
        ),
        pt=(
            "A Dependência Parcial mostra o efeito marginal de uma "
            "característica sobre a probabilidade prevista pelo modelo, "
            "calculando a média sobre a distribuição das demais características."
        ),
        de=(
            "Partielle Abhängigkeit zeigt den marginalen Effekt eines Merkmals "
            "auf die vorhergesagte Wahrscheinlichkeit des Modells, gemittelt "
            "über die Verteilung der anderen Merkmale."
        ),
        zh=("部分依赖通过对其他特征分布取平均，展示特征对模型预测概率的边际效应。"),
    )
    COLOR = "#FFA500"
    SCHEMA = PartialDependenceSchema

    def __init__(
        self,
        model: BaseModel,
        lower_percentile: float = 0.05,
        upper_percentile: float = 0.95,
        grid_resolution: int = 100,
    ):
        """Initialize a new instance of a PartialDependence explainer.

        Parameters
        ----------
        model: BaseModel
            Model to be explained.
        lower_percentile: int
            The lower and upper percentile used to limit the feature values.
            Defaults to 0.05
        upper_percentile: int
            The lower and upper percentile used to limit the feature values.
            Default to 0.95
        grid_resolution: int
            The number of equidistant points to split the range of the target
            feature. Defaults to 100.
        """

        assert upper_percentile > lower_percentile, (
            "upper_percentile value must be greater than lower_percentile"
        )

        super().__init__(model)

        self.percentiles = (lower_percentile, upper_percentile)
        self.grid_resolution = grid_resolution
        self.explanation = None

    def explain(self, dataset):
        """Method to generate the explanation

        Parameters
        ----------
        X: Tuple[DatasetDict, DatasetDict]
            Tuple with (input_samples, targets). Input samples are used to evaluate
            the partial dependence of each feature

        Returns:
        dict
            Dictionary with metadata and the partial dependence of each feature
        """
        # Lazy imports
        import numpy as np
        from sklearn.inspection import partial_dependence

        from DashAI.back.explainability.model_input import (
            as_sklearn_estimator,
            prepare_model_input,
        )

        x, y = dataset

        # scikit-learn's partial_dependence calls the estimator with plain
        # frames, bypassing the model preparation, so both splits are moved
        # into the model feature space here and the model is reached through
        # an adapter over its prepared-matrix hooks.
        x_test_dataset = prepare_model_input(self.model, x["test"])
        x_test = x_test_dataset.to_pandas()

        types = prepare_model_input(self.model, x["train"]).types

        features_names = x_test_dataset.column_names

        categorical_features = [
            1 if isinstance(types[feature], Categorical) else 0
            for feature in features_names
        ]

        output_column = list(y["test"].column_names)[0]
        categories = y["test"].types[output_column].categories
        # Categories is now a list, but handle pa.Array for backward compatibility
        if isinstance(categories, list):
            target_names = categories
        else:
            target_names = categories.to_pylist()

        explanation = {"metadata": {"target_names": target_names}}

        # Convert model to a sklearn estimator for compatibility
        estimator = as_sklearn_estimator(self.model, classes=target_names)

        for idx in range(len(features_names)):
            pd = partial_dependence(
                estimator=estimator,
                X=x_test,
                features=idx,
                categorical_features=categorical_features,
                feature_names=features_names,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="average",
            )

            explanation[features_names[idx]] = {
                "grid_values": np.round(pd["grid_values"][0], 3).tolist(),
                "average": np.round(pd["average"], 3).tolist(),
            }

        return explanation

    def _create_plot(self, data: List[object]) -> List[GroupedArtifacts]:
        """Helper method to create the explanation plots using plotly.

        Bundles one group per feature and class curve into a single grouped
        artifact, so the frontend renders a selector over the curves instead of
        a dropdown embedded in a single figure.

        Parameters
        ----------
        data : List
            Per feature and class DataFrames with the explanation generated by
            the explainer. Each DataFrame has the curve values in its first
            column and the grid positions in ``"grid_values"``.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group (a plotly curve) per
            feature and class.
        """
        # Lazy imports
        import plotly.express as px

        groups = []
        for df in data:
            column_name = df.columns[0]
            fig = px.line(
                df,
                x=df["grid_values"],
                y=df[column_name],
                labels={"grid_values": "Feature value"},
            )
            fig.update_layout(yaxis_title="Partial Dependence")
            groups.append(
                ArtifactGroup(
                    title=column_name, artifacts=[PlotlyArtifact(payload=fig)]
                )
            )

        return [GroupedArtifacts(groups=groups)]

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Method to create the explanation plot.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per feature and class
            curve.
        """
        # Lazy import
        import pandas as pd

        explanation = explanation.copy()
        metadata = explanation.pop("metadata")
        target_names = metadata["target_names"]

        dfs = []
        for feature, data in explanation.items():
            average = data["average"]
            grid_values = data["grid_values"]

            # Binary-classification case
            if len(target_names) == 2:
                target_names = [target_names[1]]

            for target, values in zip(target_names, average):  # noqa B905
                column_name = f"Feature: {feature} - Class: {target}"
                data = pd.DataFrame({column_name: values})
                data["grid_values"] = grid_values
                dfs.append(data)

        return self._create_plot(dfs)

    def story(
        self, explanation: dict, explainer_output: Union[Artifact, ArtifactGroup]
    ) -> Optional[MultilingualString]:
        """Describe, in words, the trend of one feature/class curve.

        Classifies the curve as increasing, decreasing or non-monotonic from
        its values (the same ones plotted by :meth:`plot`), and reports the
        predicted-probability range across the feature's value range.

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.
        explainer_output : Union[Artifact, ArtifactGroup]
            One of the groups previously returned by :meth:`plot`, titled
            ``"Feature: {feature} - Class: {target}"``.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised curve group.
        """
        if not isinstance(explainer_output, ArtifactGroup):
            return None
        match = re.match(r"Feature: (.+) - Class: (.+)", explainer_output.title or "")
        if match is None:
            return None
        feature, target = match.group(1), match.group(2)
        if feature not in explanation:
            return None

        target_names = explanation["metadata"]["target_names"]
        if len(target_names) == 2:
            if target != target_names[1]:
                return None
            row_index = 0
        else:
            if target not in target_names:
                return None
            row_index = target_names.index(target)

        curve = explanation[feature]
        average = curve["average"]
        if row_index >= len(average):
            return None
        values = average[row_index]
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
                        "does not noticeably affect the predicted probability "
                        "of {target}, which stays at {start_pred}."
                    ),
                    "es": (
                        "Cambiar {feature} de {start_value} a {end_value} no "
                        "afecta de forma apreciable la probabilidad predicha "
                        "de {target}, que se mantiene en {start_pred}."
                    ),
                    "pt": (
                        "Alterar {feature} de {start_value} para {end_value} "
                        "não afeta de forma perceptível a probabilidade "
                        "prevista de {target}, que permanece em {start_pred}."
                    ),
                    "de": (
                        "Eine Änderung von {feature} von {start_value} auf "
                        "{end_value} wirkt sich nicht merklich auf die "
                        "vorhergesagte Wahrscheinlichkeit von {target} aus, "
                        "die bei {start_pred} bleibt."
                    ),
                    "zh": (
                        "将{feature}从{start_value}变化到{end_value}对"
                        "{target}的预测概率没有明显影响，其保持在"
                        "{start_pred}。"
                    ),
                },
                feature=feature,
                target=target,
                start_value=start_value,
                end_value=end_value,
                start_pred=values[0],
            )

        if trend == "increases":
            return format_story(
                {
                    "en": (
                        "As {feature} goes from {start_value} to {end_value}, "
                        "the predicted probability of {target} increases from "
                        "{start_pred} to {end_pred}."
                    ),
                    "es": (
                        "A medida que {feature} va de {start_value} a "
                        "{end_value}, la probabilidad predicha de {target} "
                        "aumenta de {start_pred} a {end_pred}."
                    ),
                    "pt": (
                        "À medida que {feature} vai de {start_value} a "
                        "{end_value}, a probabilidade prevista de {target} "
                        "aumenta de {start_pred} para {end_pred}."
                    ),
                    "de": (
                        "Während {feature} von {start_value} auf {end_value} "
                        "steigt, nimmt die vorhergesagte Wahrscheinlichkeit "
                        "von {target} von {start_pred} auf {end_pred} zu."
                    ),
                    "zh": (
                        "随着{feature}从{start_value}变化到{end_value}，"
                        "{target}的预测概率从{start_pred}上升到{end_pred}。"
                    ),
                },
                feature=feature,
                target=target,
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
                        "the predicted probability of {target} decreases from "
                        "{start_pred} to {end_pred}."
                    ),
                    "es": (
                        "A medida que {feature} va de {start_value} a "
                        "{end_value}, la probabilidad predicha de {target} "
                        "disminuye de {start_pred} a {end_pred}."
                    ),
                    "pt": (
                        "À medida que {feature} vai de {start_value} a "
                        "{end_value}, a probabilidade prevista de {target} "
                        "diminui de {start_pred} para {end_pred}."
                    ),
                    "de": (
                        "Während {feature} von {start_value} auf {end_value} "
                        "steigt, sinkt die vorhergesagte Wahrscheinlichkeit "
                        "von {target} von {start_pred} auf {end_pred}."
                    ),
                    "zh": (
                        "随着{feature}从{start_value}变化到{end_value}，"
                        "{target}的预测概率从{start_pred}下降到{end_pred}。"
                    ),
                },
                feature=feature,
                target=target,
                start_value=start_value,
                end_value=end_value,
                start_pred=values[0],
                end_pred=values[-1],
            )

        return format_story(
            {
                "en": (
                    "As {feature} goes from {start_value} to {end_value}, "
                    "the predicted probability of {target} does not change "
                    "monotonically, ranging between {min_pred} and "
                    "{max_pred}."
                ),
                "es": (
                    "A medida que {feature} va de {start_value} a "
                    "{end_value}, la probabilidad predicha de {target} no "
                    "cambia de forma monótona, variando entre {min_pred} y "
                    "{max_pred}."
                ),
                "pt": (
                    "À medida que {feature} vai de {start_value} a "
                    "{end_value}, a probabilidade prevista de {target} não "
                    "muda de forma monótona, variando entre {min_pred} e "
                    "{max_pred}."
                ),
                "de": (
                    "Während {feature} von {start_value} auf {end_value} "
                    "steigt, ändert sich die vorhergesagte Wahrscheinlichkeit "
                    "von {target} nicht monoton und schwankt zwischen "
                    "{min_pred} und {max_pred}."
                ),
                "zh": (
                    "随着{feature}从{start_value}变化到{end_value}，"
                    "{target}的预测概率并非单调变化，在{min_pred}和"
                    "{max_pred}之间波动。"
                ),
            },
            feature=feature,
            target=target,
            start_value=start_value,
            end_value=end_value,
            min_pred=min(values),
            max_pred=max(values),
        )
