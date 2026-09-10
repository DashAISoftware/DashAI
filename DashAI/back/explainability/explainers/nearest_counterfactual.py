import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
    TableArtifact,
    TablePayload,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import concat_stories, format_story
from DashAI.back.models.base_model import BaseModel


class NearestCounterfactualSchema(BaseSchema):
    """Schema for NearestCounterfactual explainer hyperparameters.

    Configures how many counterfactual examples are retrieved per instance and
    the distance metric used to rank candidate examples.
    """

    n_counterfactuals: schema_field(
        int_field(ge=1, le=10),
        placeholder=3,
        description=MultilingualString(
            en=(
                "Number of counterfactual examples to retrieve for each "
                "instance. Each counterfactual is a real training example "
                "that the model classifies differently."
            ),
            es=(
                "Número de ejemplos contrafactuales a recuperar por cada "
                "instancia. Cada contrafactual es un ejemplo real de "
                "entrenamiento que el modelo clasifica de forma distinta."
            ),
            pt=(
                "Número de exemplos contrafactuais a recuperar para cada "
                "instância. Cada contrafactual é um exemplo real de "
                "treinamento que o modelo classifica de forma diferente."
            ),
            zh=(
                "为每个实例检索的反事实示例数量。每个反事实都是模型分类不同的真实训练样本。"
            ),
            de=(
                "Anzahl der kontrafaktischen Beispiele pro Instanz. Jedes "
                "kontrafaktische Beispiel ist ein echtes Trainingsbeispiel, "
                "das das Modell anders klassifiziert."
            ),
        ),
        alias=MultilingualString(
            en="Number of counterfactuals",
            es="Número de contrafactuales",
            pt="Número de contrafactuais",
            zh="反事实数量",
            de="Anzahl kontrafaktischer Beispiele",
        ),
    )  # type: ignore

    distance: schema_field(
        enum_field(enum=["l1", "l2"]),
        placeholder="l1",
        description=MultilingualString(
            en=(
                "Distance used to rank candidate counterfactuals. Numeric "
                "features are normalized by their range; non-numeric features "
                "add a constant penalty when they differ."
            ),
            es=(
                "Distancia usada para ordenar los contrafactuales candidatos. "
                "Las características numéricas se normalizan por su rango; "
                "las no numéricas agregan una penalización constante cuando "
                "difieren."
            ),
            pt=(
                "Distância usada para ordenar os contrafactuais candidatos. "
                "As características numéricas são normalizadas pelo seu "
                "intervalo; as não numéricas adicionam uma penalização "
                "constante quando diferem."
            ),
            zh=(
                "用于对候选反事实排序的距离。数值特征按范围归一化；非数值特征在不同时增加固定惩罚。"
            ),
            de=(
                "Distanz zur Rangordnung der kontrafaktischen Kandidaten. "
                "Numerische Merkmale werden über ihren Wertebereich "
                "normalisiert; nicht numerische Merkmale erhalten bei "
                "Abweichung eine konstante Strafe."
            ),
        ),
        alias=MultilingualString(
            en="Distance metric",
            es="Métrica de distancia",
            pt="Métrica de distância",
            zh="距离度量",
            de="Distanzmetrik",
        ),
    )  # type: ignore


class NearestCounterfactual(BaseLocalExplainer):
    """Case-based counterfactual explainer for tabular classification.

    For each instance to explain, this explainer answers "what would have to
    be different for the model to predict another class?" by retrieving the
    nearest real training examples that the model classifies differently
    (nearest unlike neighbors). Because counterfactuals are actual dataset
    rows, they are always plausible and never out of distribution, unlike
    synthetic perturbation-based counterfactuals.

    The explainer is fully model agnostic: it only queries ``predict``.

    References
    ----------
    - [1] Wachter, S., Mittelstadt, B. & Russell, C. (2017). "Counterfactual
           Explanations without Opening the Black Box." Harvard JOLT 31(2).
           https://arxiv.org/abs/1711.00399
    - [2] Keane, M.T. & Smyth, B. (2020). "Good Counterfactuals and Where to
           Find Them." ICCBR 2020. https://arxiv.org/abs/2005.13997
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Nearest Counterfactual",
        es="Contrafactual más cercano",
        pt="Contrafactual mais próximo",
        zh="最近反事实",
        de="Nächstes kontrafaktisches Beispiel",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Finds the closest real examples classified differently by the "
            "model, showing which feature changes would flip the prediction."
        ),
        es=(
            "Encuentra los ejemplos reales más cercanos clasificados de forma "
            "distinta por el modelo, mostrando qué cambios de características "
            "invertirían la predicción."
        ),
        pt=(
            "Encontra os exemplos reais mais próximos classificados de forma "
            "diferente pelo modelo, mostrando quais mudanças de "
            "características inverteriam a previsão."
        ),
        zh=("查找模型分类不同的最近真实示例，展示哪些特征变化会翻转预测。"),
        de=(
            "Findet die nächstgelegenen realen Beispiele, die das Modell "
            "anders klassifiziert, und zeigt, welche Merkmalsänderungen die "
            "Vorhersage kippen würden."
        ),
    )
    COLOR = "#7B1FA2"
    SCHEMA = NearestCounterfactualSchema

    def __init__(
        self,
        model: BaseModel,
        n_counterfactuals: int = 3,
        distance: str = "l1",
    ) -> None:
        """Initialize a new instance of a NearestCounterfactual explainer.

        Parameters
        ----------
        model : BaseModel
            Model to be explained.
        n_counterfactuals : int
            Number of counterfactual examples retrieved per instance.
        distance : str
            Distance used to rank candidates: 'l1' or 'l2'.
        """
        super().__init__(model)
        self.n_counterfactuals = n_counterfactuals
        self.distance = distance

    def fit(self, background_dataset, **kwargs):
        """Store the background data and its model predictions.

        Parameters
        ----------
        background_dataset : Tuple[DatasetDict, DatasetDict]
            Tuple ``(x, y)`` with the dataset splits. The train split is used
            as the pool of counterfactual candidates.
        **kwargs : Any
            Ignored; present for interface compatibility.

        Returns
        -------
        NearestCounterfactual
            The fitted explainer instance (``self``).
        """
        import numpy as np

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = background_dataset
        # Candidates and explained instances are compared feature by feature,
        # so both are kept in the model feature space. predict() keeps taking
        # the raw split, since it applies that preparation itself.
        x_train = x["train"]
        x_train_prepared = prepare_model_input(self.model, x_train)
        y_train = y["train"]

        self.background_data = x_train_prepared.to_pandas()
        self.feature_names = list(x_train_prepared.column_names)

        background_probs = self.model.predict(x_train)
        self.background_classes = np.argmax(np.asarray(background_probs), axis=1)

        # Per-feature range for numeric columns, used to normalize distances.
        self._numeric_columns = [
            column
            for column in self.background_data.columns
            if np.issubdtype(self.background_data[column].dtype, np.number)
        ]
        ranges = {}
        for column in self._numeric_columns:
            column_range = float(
                self.background_data[column].max() - self.background_data[column].min()
            )
            ranges[column] = column_range if column_range > 0 else 1.0
        self._ranges = ranges

        output_column = y_train.column_names[0]
        target_names = y_train.types[output_column].categories
        self.metadata = {
            "feature_names": self.feature_names,
            "target_names": list(target_names),
        }

        return self

    def _distances(self, instance_row, candidates):
        """Compute normalized distances between one instance and candidates.

        Parameters
        ----------
        instance_row : pd.Series
            The instance to explain.
        candidates : pd.DataFrame
            Candidate counterfactual rows.

        Returns
        -------
        np.ndarray
            One distance per candidate row.
        """
        import numpy as np

        total = np.zeros(len(candidates), dtype=float)
        for column in candidates.columns:
            if column in self._ranges:
                diff = (
                    np.abs(
                        candidates[column].to_numpy(dtype=float)
                        - float(instance_row[column])
                    )
                    / self._ranges[column]
                )
                total += diff if self.distance == "l1" else diff**2
            else:
                mismatch = (
                    candidates[column].to_numpy() != instance_row[column]
                ).astype(float)
                total += mismatch

        return np.sqrt(total) if self.distance == "l2" else total

    def explain_instance(self, instances):
        """Retrieve the nearest counterfactual examples for each instance.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            Dictionary with, for each instance, the model prediction and the
            retrieved counterfactual examples.
        """
        import numpy as np

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.explainability.model_input import prepare_model_input

        dataset = to_dashai_dataset(instances)
        X = prepare_model_input(self.model, dataset).to_pandas()

        predictions = np.asarray(self.model.predict(dataset))

        explanation = {"metadata": self.metadata}
        for i, (_, instance_row) in enumerate(X.iterrows()):
            predicted_class = int(np.argmax(predictions[i]))

            candidate_mask = self.background_classes != predicted_class
            candidates = self.background_data[candidate_mask]

            counterfactuals = []
            if len(candidates) > 0:
                distances = self._distances(instance_row, candidates)
                order = np.argsort(distances)[: self.n_counterfactuals]
                for rank in order:
                    row = candidates.iloc[int(rank)]
                    changed_features = [
                        feature
                        for feature in self.feature_names
                        if row[feature] != instance_row[feature]
                    ]
                    candidate_index = int(candidates.index[int(rank)])
                    counterfactuals.append(
                        {
                            "values": row.tolist(),
                            "predicted_class": int(
                                self.background_classes[
                                    self.background_data.index.get_loc(candidate_index)
                                ]
                            ),
                            "distance": float(np.round(distances[int(rank)], 4)),
                            "changed_features": changed_features,
                        }
                    )

            explanation[i] = {
                "instance_values": instance_row.tolist(),
                "model_prediction": predictions[i].tolist(),
                "predicted_class": predicted_class,
                "counterfactuals": counterfactuals,
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each instance as a comparison table.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained instance,
            each holding that instance's comparison table.
        """
        exp = explanation.copy()
        metadata = exp.pop("metadata")
        feature_names = metadata["feature_names"]
        target_names = metadata["target_names"]

        groups = []
        for i in exp:
            instance = exp[i]
            instance_values = instance["instance_values"]
            predicted_class = instance["predicted_class"]
            predicted_name = target_names[predicted_class]
            counterfactuals = instance["counterfactuals"]

            columns = ["Feature", "Instance"] + [
                f"Counterfactual {k + 1}" for k in range(len(counterfactuals))
            ]
            rows = []
            highlight = []
            for row_idx, feature in enumerate(feature_names):
                row = [feature, instance_values[row_idx]]
                for cf_idx, counterfactual in enumerate(counterfactuals):
                    row.append(counterfactual["values"][row_idx])
                    if feature in counterfactual["changed_features"]:
                        highlight.append({"row": row_idx, "column": 2 + cf_idx})
                rows.append(row)

            prediction_row = ["Predicted class", predicted_name] + [
                target_names[counterfactual["predicted_class"]]
                for counterfactual in counterfactuals
            ]
            rows.append(prediction_row)
            for cf_idx in range(len(counterfactuals)):
                highlight.append({"row": len(feature_names), "column": 2 + cf_idx})

            title = f"Instance {int(i) + 1}"
            table = TableArtifact(
                payload=TablePayload(columns=columns, rows=rows, highlight=highlight),
            )
            groups.append(ArtifactGroup(title=title, artifacts=[table]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction and each nearest counterfactual.

        Names the predicted class and probability, then lists every
        counterfactual with the features it changed, the class it yields and
        its distance to the instance (the same values shown in the
        comparison table from :meth:`plot`).

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
        target_names = metadata["target_names"]
        instance = explanation[index]

        predicted_class = instance["predicted_class"]
        predicted_name = target_names[predicted_class]
        predicted_prob = round(instance["model_prediction"][predicted_class], 3)
        counterfactuals = instance["counterfactuals"]

        if not counterfactuals:
            return format_story(
                {
                    "en": (
                        "The model predicted {predicted_name} "
                        "(p={predicted_prob}). No counterfactual examples "
                        "were found in the training data."
                    ),
                    "es": (
                        "El modelo predijo {predicted_name} "
                        "(p={predicted_prob}). No se encontraron ejemplos "
                        "contrafactuales en los datos de entrenamiento."
                    ),
                    "pt": (
                        "O modelo previu {predicted_name} "
                        "(p={predicted_prob}). Não foram encontrados "
                        "exemplos contrafactuais nos dados de treinamento."
                    ),
                    "de": (
                        "Das Modell sagte {predicted_name} "
                        "(p={predicted_prob}) voraus. Im Trainingsdatensatz "
                        "wurden keine kontrafaktischen Beispiele gefunden."
                    ),
                    "zh": (
                        "模型预测为{predicted_name}（p={predicted_prob}）。"
                        "在训练数据中未找到反事实样本。"
                    ),
                },
                predicted_name=predicted_name,
                predicted_prob=predicted_prob,
            )

        story = format_story(
            {
                "en": "The model predicted {predicted_name} (p={predicted_prob}).",
                "es": "El modelo predijo {predicted_name} (p={predicted_prob}).",
                "pt": "O modelo previu {predicted_name} (p={predicted_prob}).",
                "de": "Das Modell sagte {predicted_name} (p={predicted_prob}) voraus.",
                "zh": "模型预测为{predicted_name}（p={predicted_prob}）。",
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
        )

        for cf_idx, counterfactual in enumerate(counterfactuals):
            cf_name = target_names[counterfactual["predicted_class"]]
            changed_features = counterfactual["changed_features"]
            distance = counterfactual["distance"]
            if changed_features:
                changed = ", ".join(changed_features)
                line = format_story(
                    {
                        "en": (
                            "Counterfactual {n}: changing {changed} yields "
                            "{cf_name} (distance {distance})."
                        ),
                        "es": (
                            "Contrafactual {n}: cambiando {changed} se "
                            "obtiene {cf_name} (distancia {distance})."
                        ),
                        "pt": (
                            "Contrafactual {n}: alterando {changed} obtém-se "
                            "{cf_name} (distância {distance})."
                        ),
                        "de": (
                            "Kontrafaktisch {n}: Durch Ändern von {changed} "
                            "ergibt sich {cf_name} (Distanz {distance})."
                        ),
                        "zh": (
                            "反事实{n}：改变{changed}会得到{cf_name}"
                            "（距离{distance}）。"
                        ),
                    },
                    n=cf_idx + 1,
                    changed=changed,
                    cf_name=cf_name,
                    distance=distance,
                )
            else:
                line = format_story(
                    {
                        "en": (
                            "Counterfactual {n}: changing nothing yields "
                            "{cf_name} (distance {distance})."
                        ),
                        "es": (
                            "Contrafactual {n}: sin cambiar nada se obtiene "
                            "{cf_name} (distancia {distance})."
                        ),
                        "pt": (
                            "Contrafactual {n}: sem alterar nada obtém-se "
                            "{cf_name} (distância {distance})."
                        ),
                        "de": (
                            "Kontrafaktisch {n}: Ohne Änderungen ergibt sich "
                            "{cf_name} (Distanz {distance})."
                        ),
                        "zh": (
                            "反事实{n}：不改变任何特征即可得到"
                            "{cf_name}（距离{distance}）。"
                        ),
                    },
                    n=cf_idx + 1,
                    cf_name=cf_name,
                    distance=distance,
                )
            story = concat_stories(story, line, separator="\n")

        return story
