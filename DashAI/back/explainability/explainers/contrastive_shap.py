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
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class ContrastiveShapSchema(BaseSchema):
    """Schema for ContrastiveShap explainer hyperparameters.

    Configures the foil class the explanation contrasts against and the
    background sampling used to fit the underlying SHAP explainer.
    """

    foil_class: schema_field(
        string_field(),
        placeholder="second_most_probable",
        description=MultilingualString(
            en=(
                "Class to contrast against (the foil in 'why P rather than "
                "Q?'). Enter an exact class name, or leave "
                "'second_most_probable' to contrast against the runner-up "
                "class of each instance."
            ),
            es=(
                "Clase contra la que se contrasta (el foil en '¿por qué P y "
                "no Q?'). Ingrese un nombre de clase exacto, o deje "
                "'second_most_probable' para contrastar con la segunda clase "
                "más probable de cada instancia."
            ),
            pt=(
                "Classe contra a qual contrastar (o foil em 'por que P e não "
                "Q?'). Insira um nome de classe exato, ou deixe "
                "'second_most_probable' para contrastar com a segunda classe "
                "mais provável de cada instância."
            ),
            zh=(
                "对比的目标类别（'为什么是P而不是Q'中的Q）。"
                "输入准确的类别名称，或保留'second_most_probable'以对比每个实例的第二可能类别。"
            ),
            de=(
                "Klasse, gegen die kontrastiert wird (das Foil in 'warum P "
                "statt Q?'). Geben Sie einen exakten Klassennamen ein oder "
                "belassen Sie 'second_most_probable', um gegen die "
                "zweitwahrscheinlichste Klasse zu kontrastieren."
            ),
        ),
        alias=MultilingualString(
            en="Foil class",
            es="Clase foil",
            pt="Classe foil",
            zh="对比类别",
            de="Foil-Klasse",
        ),
    )  # type: ignore

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
                "如果需要对背景数据进行采样则为'true'；否则使用整个训练集。较小的数据集可加速算法运行。"
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
            zh=("如果选择了'采样背景数据'，则为从训练集中抽取的背景样本比例。"),
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


class ContrastiveShap(BaseLocalExplainer):
    """Contrastive local explainer: why class P rather than class Q?

    Standard attribution methods answer "why did the model predict P?".
    Contrastive explanations answer the question people actually ask: "why P
    rather than Q?". This explainer computes Kernel SHAP attributions for both
    the predicted class (the fact) and a contrast class (the foil), and
    reports the per-feature difference. Features with a large positive delta
    are the ones that pushed the model towards the fact and away from the
    foil.

    The foil can be a fixed class name, or the second most probable class of
    each instance (default).

    References
    ----------
    - [1] Miller, T. (2019). "Explanation in Artificial Intelligence:
           Insights from the Social Sciences." Artificial Intelligence 267.
           https://arxiv.org/abs/1706.07269
    - [2] Lundberg, S.M. & Lee, S.I. (2017). "A Unified Approach to
           Interpreting Model Predictions." NeurIPS 30.
           https://arxiv.org/abs/1705.07874
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Contrastive SHAP (why P rather than Q)",
        es="SHAP contrastivo (por qué P y no Q)",
        pt="SHAP contrastivo (por que P e não Q)",
        zh="对比SHAP（为什么是P而不是Q）",
        de="Kontrastives SHAP (warum P statt Q)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Explains why the model predicted one class rather than another "
            "by contrasting SHAP attributions between the two classes."
        ),
        es=(
            "Explica por qué el modelo predijo una clase y no otra, "
            "contrastando las atribuciones SHAP entre ambas clases."
        ),
        pt=(
            "Explica por que o modelo previu uma classe e não outra, "
            "contrastando as atribuições SHAP entre as duas classes."
        ),
        zh=("通过对比两个类别之间的SHAP归因，解释模型为什么预测一个类别而不是另一个。"),
        de=(
            "Erklärt, warum das Modell eine Klasse statt einer anderen "
            "vorhergesagt hat, durch Kontrastierung der SHAP-Attributionen "
            "beider Klassen."
        ),
    )
    COLOR = "#00695C"
    SCHEMA = ContrastiveShapSchema

    def __init__(
        self,
        model: BaseModel,
        foil_class: str = "second_most_probable",
    ) -> None:
        """Initialize a new instance of a ContrastiveShap explainer.

        Parameters
        ----------
        model : BaseModel
            Model to be explained.
        foil_class : str
            Name of the class to contrast against, or
            'second_most_probable' to use the runner-up class per instance.
        """
        super().__init__(model)
        self.foil_class = foil_class

    def fit(
        self,
        background_dataset,
        sample_background_data=False,
        background_fraction=None,
        **kwargs,
    ):
        """Fit the underlying Kernel SHAP explainer on background data.

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
        ContrastiveShap
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

        output_column = y_train.column_names[0]
        target_names = y_train.types[output_column].categories
        self.metadata = {
            "feature_names": feature_names,
            "target_names": list(target_names),
        }

        return self

    def _resolve_foil(self, prediction, fact_class: int) -> int:
        """Resolve the foil class index for one instance.

        Parameters
        ----------
        prediction : np.ndarray
            Per-class probabilities for the instance.
        fact_class : int
            Index of the predicted (fact) class.

        Returns
        -------
        int
            Index of the foil class. Falls back to the second most probable
            class when the configured name is unknown or equals the fact.
        """
        import numpy as np

        target_names = self.metadata["target_names"]
        if self.foil_class in target_names:
            foil = target_names.index(self.foil_class)
            if foil != fact_class:
                return foil

        order = np.argsort(prediction)[::-1]
        return int(order[1]) if len(order) > 1 else fact_class

    def explain_instance(self, instances):
        """Compute contrastive SHAP attributions for the given instances.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            Dictionary with, for each instance, the fact and foil classes and
            the per-feature attribution difference (fact minus foil).
        """
        import numpy as np

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.explainability.model_input import prepare_model_input

        dataset = to_dashai_dataset(instances)
        X = prepare_model_input(self.model, dataset).to_pandas()

        predictions = np.asarray(self.model.predict(dataset))

        shap_values = self.explainer.shap_values(X=X)
        # (n_instances, n_features, n_classes) -> (n_instances, n_classes,
        # n_features), same normalization used by the KernelShap explainer.
        shap_values = np.array(shap_values).transpose(0, 2, 1)

        explanation = {"metadata": self.metadata}
        for i, (instance, prediction, contributions) in enumerate(
            zip(X.to_numpy(), predictions, shap_values)  # noqa: B905
        ):
            fact_class = int(np.argmax(prediction))
            foil_class = self._resolve_foil(prediction, fact_class)
            delta = contributions[fact_class] - contributions[foil_class]

            explanation[i] = {
                "instance_values": instance.tolist(),
                "model_prediction": prediction.tolist(),
                "fact_class": fact_class,
                "foil_class": foil_class,
                "fact_shap_values": np.round(contributions[fact_class], 3).tolist(),
                "foil_shap_values": np.round(contributions[foil_class], 3).tolist(),
                "delta_values": np.round(delta, 3).tolist(),
            }

        return explanation

    def _create_plot(self, data, fact_name, foil_name, fact_prob, foil_prob):
        """Create the contrastive bar plot for one instance.

        Parameters
        ----------
        data : pd.DataFrame
            Dataframe with 'label' and 'delta' columns, sorted for plotting.
        fact_name : str
            Name of the predicted class.
        foil_name : str
            Name of the foil class.
        fact_prob : float
            Predicted probability of the fact class.
        foil_prob : float
            Predicted probability of the foil class.

        Returns
        -------
        plotly.graph_objs.Figure
            The Plotly figure.
        """
        import plotly.graph_objs as go

        colors = [
            "rgb(231,63,116)" if value >= 0 else "rgb(47,138,196)"
            for value in data["delta"]
        ]

        fig = go.Figure(
            go.Bar(
                x=data["delta"],
                y=data["label"],
                orientation="h",
                marker={"color": colors},
                text=data["delta"],
                textposition="auto",
            )
        )

        fig.update_layout(
            title={
                "text": (
                    f"Why {fact_name} (p={fact_prob}) rather than "
                    f"{foil_name} (p={foil_prob})?"
                ),
                "font": {"size": 14},
            },
            margin={"pad": 20, "l": 100, "r": 60, "t": 60, "b": 40},
            xaxis={"title_text": "Attribution difference (fact - foil)"},
            yaxis={"showgrid": True},
        )

        return fig

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each instance as a contrastive bar plot.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained instance,
            each holding that instance's contrastive plot.
        """
        import numpy as np
        import pandas as pd

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        feature_names = metadata["feature_names"]
        target_names = metadata["target_names"]
        max_features = 8

        groups = []
        for i in exp:
            instance = exp[i]
            fact_class = instance["fact_class"]
            foil_class = instance["foil_class"]
            fact_name = target_names[fact_class]
            foil_name = target_names[foil_class]
            prediction = instance["model_prediction"]
            fact_prob = float(np.round(prediction[fact_class], 3))
            foil_prob = float(np.round(prediction[foil_class], 3))

            data = pd.DataFrame(
                {
                    "features": feature_names,
                    "values": instance["instance_values"],
                    "delta": instance["delta_values"],
                }
            )
            data["delta_abs"] = data["delta"].abs()
            data = data.sort_values(by="delta_abs", ascending=True)
            if len(data) > max_features:
                data = data.iloc[-max_features:, :]
            data["label"] = data["features"] + "=" + data["values"].map(str)

            title = f"Instance {int(i) + 1}"
            fig = self._create_plot(data, fact_name, foil_name, fact_prob, foil_prob)
            plot = PlotlyArtifact(payload=fig)

            groups.append(ArtifactGroup(title=title, artifacts=[plot]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, why the fact class beat the foil class.

        Names the fact and foil classes, their probabilities, and the top-3
        features by ``|fact - foil|`` attribution difference (the same
        values plotted by :meth:`plot`).

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
        target_names = metadata["target_names"]
        instance = explanation[index]

        fact_class = instance["fact_class"]
        foil_class = instance["foil_class"]
        fact_name = target_names[fact_class]
        foil_name = target_names[foil_class]
        prediction = instance["model_prediction"]
        fact_prob = round(prediction[fact_class], 3)
        foil_prob = round(prediction[foil_class], 3)

        ranking = sorted(
            zip(
                feature_names,
                instance["instance_values"],
                instance["delta_values"],
                strict=True,
            ),
            key=lambda row: abs(row[2]),
            reverse=True,
        )
        top = ranking[:3]
        top_features = ", ".join(f"{name}={value}" for name, value, _ in top)

        return format_story(
            {
                "en": (
                    "The model predicted {fact_name} (p={fact_prob}) rather "
                    "than {foil_name} (p={foil_prob}) mainly because of: "
                    "{top_features}."
                ),
                "es": (
                    "El modelo predijo {fact_name} (p={fact_prob}) en lugar "
                    "de {foil_name} (p={foil_prob}) principalmente por: "
                    "{top_features}."
                ),
                "pt": (
                    "O modelo previu {fact_name} (p={fact_prob}) em vez de "
                    "{foil_name} (p={foil_prob}) principalmente por: "
                    "{top_features}."
                ),
                "de": (
                    "Das Modell sagte eher {fact_name} (p={fact_prob}) als "
                    "{foil_name} (p={foil_prob}) voraus, hauptsächlich "
                    "aufgrund von: {top_features}."
                ),
                "zh": (
                    "模型预测为{fact_name}（p={fact_prob}）而非{foil_name}"
                    "（p={foil_prob}），主要原因是：{top_features}。"
                ),
            },
            fact_name=fact_name,
            fact_prob=fact_prob,
            foil_name=foil_name,
            foil_prob=foil_prob,
            top_features=top_features,
        )
