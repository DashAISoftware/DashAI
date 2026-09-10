import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class RegressionKernelShapSchema(BaseSchema):
    """Schema for the regression Kernel SHAP explainer hyperparameters.

    Configures the background sampling used to fit the SHAP explainer.
    """

    fit_parameter_sample_background_data: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "'true' if background data must be sampled; otherwise the "
                "entire training set is used. Smaller datasets speed up the "
                "algorithm runtime."
            ),
            es=(
                "'true' si se deben muestrear los datos de fondo; de lo "
                "contrario se usa el conjunto de entrenamiento completo. "
                "Conjuntos más pequeños reducen el tiempo de ejecución."
            ),
            pt=(
                "'true' se os dados de fundo devem ser amostrados; caso "
                "contrário, usa-se o conjunto de treinamento completo. "
                "Conjuntos menores reduzem o tempo de execução."
            ),
            zh=(
                "如果需要对背景数据进行采样则为'true'；"
                "否则使用整个训练集。较小的数据集可加速算法运行。"
            ),
            de=(
                "'true', wenn Hintergrunddaten gesamplet werden müssen; sonst "
                "wird der gesamte Trainingssatz verwendet. Kleinere "
                "Datensätze beschleunigen die Laufzeit."
            ),
        ),
        alias=MultilingualString(
            en="Sample background data",
            es="Muestrear datos de fondo",
            pt="Amostrar dados de fundo",
            zh="采样背景数据",
            de="Hintergrunddaten samplen",
        ),
    )  # type: ignore

    fit_parameter_background_fraction: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en=(
                "If 'Sample background data' is selected, fraction of "
                "background samples to draw from the training set."
            ),
            es=(
                "Si se selecciona 'Muestrear datos de fondo', proporción de "
                "muestras de fondo a extraer del conjunto de entrenamiento."
            ),
            pt=(
                "Se 'Amostrar dados de fundo' estiver selecionado, fração de "
                "amostras de fundo a extrair do conjunto de treinamento."
            ),
            zh="如果选择了'采样背景数据'，则为从训练集中抽取的背景样本比例。",
            de=(
                "Wenn 'Hintergrunddaten samplen' ausgewählt ist, Anteil der "
                "Hintergrundproben aus dem Trainingssatz."
            ),
        ),
        alias=MultilingualString(
            en="Background fraction",
            es="Fracción de fondo",
            pt="Fração de fundo",
            zh="背景比例",
            de="Hintergrundfraktion",
        ),
    )  # type: ignore


class RegressionKernelShap(BaseLocalExplainer):
    """Model agnostic local explainer for regression via Kernel SHAP.

    For each instance, estimates how much each feature value pushed the
    model's numeric prediction above or below the expected (baseline) output,
    using the Kernel SHAP weighted linear model over sampled feature
    coalitions. The model is treated as a black box: only ``predict`` is
    queried.

    References
    ----------
    - [1] Lundberg, S.M. & Lee, S.I. (2017). "A Unified Approach to
           Interpreting Model Predictions." NeurIPS 30.
           https://arxiv.org/abs/1705.07874
    - [2] https://shap.readthedocs.io/en/latest/generated/shap.KernelExplainer.html
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME = MultilingualString(
        en="Kernel SHAP (regression)",
        es="Kernel SHAP (regresión)",
        pt="Kernel SHAP (regressão)",
        zh="Kernel SHAP（回归）",
        de="Kernel SHAP (Regression)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Attributes a regression model's numeric prediction to each "
            "feature value using SHAP values."
        ),
        es=(
            "Atribuye la predicción numérica de un modelo de regresión a cada "
            "valor de característica usando valores SHAP."
        ),
        pt=(
            "Atribui a previsão numérica de um modelo de regressão a cada "
            "valor de característica usando valores SHAP."
        ),
        zh="使用SHAP值将回归模型的数值预测归因于每个特征值。",
        de=(
            "Ordnet die numerische Vorhersage eines Regressionsmodells jedem "
            "Merkmalswert mittels SHAP-Werten zu."
        ),
    )
    COLOR = "#00838F"
    SCHEMA = RegressionKernelShapSchema

    def __init__(self, model: BaseModel) -> None:
        """Initialize a new instance of a RegressionKernelShap explainer.

        Parameters
        ----------
        model : BaseModel
            Regression model to be explained.
        """
        super().__init__(model)

    def fit(
        self,
        background_dataset,
        sample_background_data=False,
        background_fraction=None,
        **kwargs,
    ):
        """Fit the Kernel SHAP explainer on background data.

        Parameters
        ----------
        background_dataset : Tuple[DatasetDict, DatasetDict]
            Tuple ``(x, y)`` with the dataset splits; the train split is used
            as SHAP background data.
        sample_background_data : bool
            True if the background data must be sampled.
        background_fraction : float
            Fraction of the training samples used as background data when
            ``sample_background_data`` is True.
        **kwargs : Any
            Ignored; present for interface compatibility.

        Returns
        -------
        RegressionKernelShap
            The fitted explainer instance (``self``).
        """
        import shap

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = background_dataset
        # SHAP calls the model with perturbed matrices, so the background must
        # be in the model feature space and the model must be queried through
        # predict_prepared.
        x_train = prepare_model_input(self.model, x["train"])
        y_train = y["train"]

        background_data = x_train.to_pandas()
        feature_names = list(x_train.column_names)

        if bool(sample_background_data) and background_fraction:
            n_samples = max(1, int(background_fraction * len(background_data)))
            background_data = shap.sample(background_data, n_samples)

        self.explainer = shap.KernelExplainer(
            model=self.model.predict_prepared,
            data=background_data,
            feature_names=feature_names,
        )

        self.metadata = {
            "feature_names": feature_names,
            "output_column": y_train.column_names[0],
        }

        return self

    def explain_instance(self, instances):
        """Compute SHAP values for each instance.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            Dictionary with, for each instance, the model prediction, the
            baseline value and the per-feature SHAP values.
        """
        import numpy as np

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.explainability.model_input import prepare_model_input

        dataset = to_dashai_dataset(instances)
        X = prepare_model_input(self.model, dataset).to_pandas()

        predictions = np.asarray(self.model.predict(dataset)).ravel()

        shap_values = np.asarray(self.explainer.shap_values(X=X))
        # Single-output models may yield (n, n_features) or (n, n_features, 1).
        if shap_values.ndim == 3:
            shap_values = shap_values[..., 0]

        base_value = np.asarray(self.explainer.expected_value).ravel()[0]

        explanation = {
            "metadata": self.metadata,
            "base_value": float(np.round(base_value, 3)),
        }
        for i, (instance, prediction, contributions) in enumerate(
            zip(X.to_numpy(), predictions, shap_values, strict=True)
        ):
            explanation[i] = {
                "instance_values": instance.tolist(),
                "model_prediction": float(np.round(prediction, 3)),
                "shap_values": np.round(contributions, 3).tolist(),
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each instance as a SHAP bar plot.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained instance,
            each holding that instance's plotly plot.
        """
        import pandas as pd
        import plotly.graph_objs as go

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        base_value = exp.pop("base_value")
        feature_names = metadata["feature_names"]
        output_column = metadata["output_column"]
        max_features = 8

        groups = []
        for i in exp:
            instance = exp[i]
            prediction = instance["model_prediction"]

            data = pd.DataFrame(
                {
                    "features": feature_names,
                    "values": instance["instance_values"],
                    "shap_values": instance["shap_values"],
                }
            )
            data["shap_abs"] = data["shap_values"].abs()
            data = data.sort_values(by="shap_abs", ascending=True)
            if len(data) > max_features:
                data = data.iloc[-max_features:, :]
            data["label"] = data["features"] + "=" + data["values"].map(str)

            colors = [
                "rgb(231,63,116)" if value >= 0 else "rgb(47,138,196)"
                for value in data["shap_values"]
            ]
            fig = go.Figure(
                go.Bar(
                    x=data["shap_values"],
                    y=data["label"],
                    orientation="h",
                    marker={"color": colors},
                    text=data["shap_values"],
                    textposition="auto",
                )
            )
            fig.update_layout(
                title={
                    "text": (
                        f"{output_column}: prediction f(x)={prediction}, "
                        f"baseline E[f(x)]={base_value}"
                    ),
                    "font": {"size": 14},
                },
                margin={"pad": 20, "l": 100, "r": 60, "t": 60, "b": 40},
                xaxis={"title_text": "SHAP value (impact on prediction)"},
                yaxis={"showgrid": True},
            )

            title = f"Instance {int(i) + 1}"
            plot = PlotlyArtifact(payload=fig)

            groups.append(ArtifactGroup(title=title, artifacts=[plot]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the predicted value and its top contributors.

        Names the predicted value, its offset from the baseline, and the
        top-3 features by absolute SHAP value (the same values plotted by
        :meth:`plot`).

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain_instance`.
        explainer_output : ArtifactGroup
            The group previously returned by :meth:`plot`, titled
            ``"Instance {n}"``.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised "Instance N" group.
        """
        match = re.match(r"Instance (\d+)", explainer_output.title or "")
        if match is None:
            return None
        index = int(match.group(1)) - 1
        if index not in explanation:
            return None

        metadata = explanation["metadata"]
        feature_names = metadata["feature_names"]
        output_column = metadata["output_column"]
        base_value = explanation["base_value"]
        instance = explanation[index]

        prediction = instance["model_prediction"]
        delta = round(prediction - base_value, 3)

        ranking = sorted(
            zip(
                feature_names,
                instance["instance_values"],
                instance["shap_values"],
                strict=True,
            ),
            key=lambda row: abs(row[2]),
            reverse=True,
        )
        top = ranking[:3]
        top_features = ", ".join(
            f"{name}={value} ({shap:+})" for name, value, shap in top
        )

        return format_story(
            {
                "en": (
                    "The model predicted {output_column}={prediction}, "
                    "{delta:+} from the baseline {base_value}. Main "
                    "contributions: {top_features}."
                ),
                "es": (
                    "El modelo predijo {output_column}={prediction}, "
                    "{delta:+} respecto a la base {base_value}. "
                    "Contribuciones principales: {top_features}."
                ),
                "pt": (
                    "O modelo previu {output_column}={prediction}, "
                    "{delta:+} em relação à base {base_value}. "
                    "Principais contribuições: {top_features}."
                ),
                "de": (
                    "Das Modell sagte {output_column}={prediction} voraus, "
                    "{delta:+} gegenüber der Basislinie {base_value}. "
                    "Wichtigste Beiträge: {top_features}."
                ),
                "zh": (
                    "模型预测{output_column}={prediction}，相对基线"
                    "{base_value}的差值为{delta:+}。主要贡献："
                    "{top_features}。"
                ),
            },
            output_column=output_column,
            prediction=prediction,
            delta=delta,
            base_value=base_value,
            top_features=top_features,
        )
