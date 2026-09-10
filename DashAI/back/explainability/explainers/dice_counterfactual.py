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
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import concat_stories, format_story
from DashAI.back.models.base_model import BaseModel


class DiceCounterfactualSchema(BaseSchema):
    """Schema for the DiCE counterfactual explainer hyperparameters.

    Configures how many counterfactuals are generated, the generation
    method and the class the counterfactuals should reach.
    """

    total_cfs: schema_field(
        int_field(ge=1, le=10),
        placeholder=3,
        description=MultilingualString(
            en="Number of counterfactual examples to generate per instance.",
            es="Número de ejemplos contrafactuales a generar por instancia.",
            pt="Número de exemplos contrafactuais a gerar por instância.",
            zh="为每个实例生成的反事实示例数量。",
            de="Anzahl der pro Instanz erzeugten kontrafaktischen Beispiele.",
        ),
        alias=MultilingualString(
            en="Number of counterfactuals",
            es="Número de contrafactuales",
            pt="Número de contrafactuais",
            zh="反事实数量",
            de="Anzahl kontrafaktischer Beispiele",
        ),
    )  # type: ignore

    method: schema_field(
        enum_field(enum=["random", "genetic", "kdtree"]),
        placeholder="random",
        description=MultilingualString(
            en=(
                "Counterfactual search strategy: 'random' (random sampling of "
                "feature perturbations), 'genetic' (genetic algorithm "
                "optimizing proximity and diversity) or 'kdtree' (closest "
                "real training examples)."
            ),
            es=(
                "Estrategia de búsqueda: 'random' (muestreo aleatorio de "
                "perturbaciones), 'genetic' (algoritmo genético que optimiza "
                "proximidad y diversidad) o 'kdtree' (ejemplos reales más "
                "cercanos del entrenamiento)."
            ),
            pt=(
                "Estratégia de busca: 'random' (amostragem aleatória de "
                "perturbações), 'genetic' (algoritmo genético que otimiza "
                "proximidade e diversidade) ou 'kdtree' (exemplos reais mais "
                "próximos do treinamento)."
            ),
            zh=(
                "反事实搜索策略：'random'（随机采样特征扰动）、"
                "'genetic'（优化接近度和多样性的遗传算法）或'kdtree'（最近的真实训练样本）。"
            ),
            de=(
                "Suchstrategie: 'random' (zufällige Merkmalsstörungen), "
                "'genetic' (genetischer Algorithmus für Nähe und Diversität) "
                "oder 'kdtree' (nächstgelegene echte Trainingsbeispiele)."
            ),
        ),
        alias=MultilingualString(
            en="Search method",
            es="Método de búsqueda",
            pt="Método de busca",
            zh="搜索方法",
            de="Suchmethode",
        ),
    )  # type: ignore

    desired_class: schema_field(
        string_field(),
        placeholder="opposite",
        description=MultilingualString(
            en=(
                "Class the counterfactuals should reach. Enter an exact class "
                "name, or leave 'opposite' to target the runner-up class of "
                "each instance."
            ),
            es=(
                "Clase que los contrafactuales deben alcanzar. Ingrese un "
                "nombre de clase exacto, o deje 'opposite' para apuntar a la "
                "segunda clase más probable de cada instancia."
            ),
            pt=(
                "Classe que os contrafactuais devem alcançar. Insira um nome "
                "de classe exato, ou deixe 'opposite' para apontar à segunda "
                "classe mais provável de cada instância."
            ),
            zh="反事实应达到的类别。输入准确的类别名称，或保留'opposite'以针对每个实例的第二可能类别。",
            de=(
                "Klasse, die die kontrafaktischen Beispiele erreichen sollen. "
                "Geben Sie einen exakten Klassennamen ein oder belassen Sie "
                "'opposite' für die zweitwahrscheinlichste Klasse."
            ),
        ),
        alias=MultilingualString(
            en="Desired class",
            es="Clase deseada",
            pt="Classe desejada",
            zh="目标类别",
            de="Zielklasse",
        ),
    )  # type: ignore


class _SklearnProbaShim:
    """Adapter exposing the sklearn-native interface DiCE expects.

    DashAI classifiers override ``predict`` to return probabilities; DiCE
    expects ``predict`` to return class labels and ``predict_proba`` to
    return probabilities. DiCE queries with frames that are already in the
    model feature space, so the model is reached through its prepared-matrix
    hook.
    """

    def __init__(self, model):
        self._model = model

    def predict_proba(self, x):
        """Return the class-probability matrix for ``x``."""
        return self._model.predict_proba_prepared(x)

    def predict(self, x):
        """Return hard class labels derived from the probabilities."""
        import numpy as np

        return np.argmax(self.predict_proba(x), axis=1)


class DiceCounterfactual(BaseLocalExplainer):
    """Diverse counterfactual explanations via the DiCE library.

    For each instance, generates a set of synthetic examples that the model
    classifies as a different (desired) class while staying close to the
    original instance, answering "what minimal changes would flip this
    prediction?". Unlike the Nearest Counterfactual explainer (which returns
    real training rows), DiCE synthesizes new feature combinations and
    optimizes for both proximity and diversity.

    Note: DiCE queries the underlying estimator directly with raw feature
    values, so it is intended for datasets with numeric features.

    References
    ----------
    - [1] Mothilal, R.K., Sharma, A. & Tan, C. (2020). "Explaining Machine
           Learning Classifiers through Diverse Counterfactual Explanations."
           FAT* 2020. https://arxiv.org/abs/1905.07697
    - [2] https://github.com/interpretml/DiCE
    """

    DISPLAY_NAME = MultilingualString(
        en="DiCE Counterfactuals",
        es="Contrafactuales DiCE",
        pt="Contrafactuais DiCE",
        zh="DiCE反事实",
        de="DiCE-Kontrafaktuale",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Generates diverse synthetic examples with minimal changes that "
            "flip the model's prediction to a desired class."
        ),
        es=(
            "Genera ejemplos sintéticos diversos con cambios mínimos que "
            "invierten la predicción del modelo hacia una clase deseada."
        ),
        pt=(
            "Gera exemplos sintéticos diversos com mudanças mínimas que "
            "invertem a previsão do modelo para uma classe desejada."
        ),
        zh="生成具有最小变化的多样化合成示例，将模型预测翻转到目标类别。",
        de=(
            "Erzeugt diverse synthetische Beispiele mit minimalen Änderungen, "
            "die die Modellvorhersage zu einer gewünschten Klasse kippen."
        ),
    )
    COLOR = "#6A1B9A"
    SCHEMA = DiceCounterfactualSchema

    def __init__(
        self,
        model: BaseModel,
        total_cfs: int = 3,
        method: str = "random",
        desired_class: str = "opposite",
    ) -> None:
        """Initialize a new instance of a DiceCounterfactual explainer.

        Parameters
        ----------
        model : BaseModel
            Classification model to be explained.
        total_cfs : int
            Number of counterfactuals generated per instance.
        method : str
            DiCE search method: 'random', 'genetic' or 'kdtree'.
        desired_class : str
            Class name the counterfactuals should reach, or 'opposite' for
            the runner-up class of each instance.
        """
        super().__init__(model)
        self.total_cfs = total_cfs
        self.method = method
        self.desired_class = desired_class

    def fit(self, background_dataset, **kwargs):
        """Build the DiCE data and model interfaces from the train split.

        Parameters
        ----------
        background_dataset : Tuple[DatasetDict, DatasetDict]
            Tuple ``(x, y)`` with the dataset splits.
        **kwargs : Any
            Ignored; present for interface compatibility.

        Returns
        -------
        DiceCounterfactual
            The fitted explainer instance (``self``).
        """
        import dice_ml
        import numpy as np

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = background_dataset
        # DiCE samples the training frame and queries the model with plain
        # frames, so both must be in the model feature space.
        x_train = prepare_model_input(self.model, x["train"])
        y_train = y["train"]

        train_frame = x_train.to_pandas()
        self.feature_names = list(train_frame.columns)

        output_column = y_train.column_names[0]
        target_names = [str(c) for c in y_train.types[output_column].categories]
        self.metadata = {
            "feature_names": self.feature_names,
            "target_names": target_names,
        }
        self.output_column = output_column

        labels = y_train.to_pandas()[output_column].astype(str)
        encoded = labels.map({name: k for k, name in enumerate(target_names)})
        train_frame = train_frame.copy()
        train_frame[output_column] = encoded.to_numpy()

        continuous = [
            column
            for column in self.feature_names
            if np.issubdtype(train_frame[column].dtype, np.number)
        ]

        data_interface = dice_ml.Data(
            dataframe=train_frame,
            continuous_features=continuous,
            outcome_name=output_column,
        )
        model_interface = dice_ml.Model(
            model=_SklearnProbaShim(self.model),
            backend="sklearn",
            model_type="classifier",
        )
        self._dice = dice_ml.Dice(data_interface, model_interface, method=self.method)

        return self

    def _resolve_desired_class(self, prediction, fact_class: int):
        """Resolve DiCE's desired_class argument for one instance.

        Parameters
        ----------
        prediction : np.ndarray
            Per-class probabilities for the instance.
        fact_class : int
            Index of the predicted class.

        Returns
        -------
        int or str
            A class index, or the literal 'opposite' for binary problems.
        """
        import numpy as np

        target_names = self.metadata["target_names"]
        if self.desired_class in target_names:
            desired = target_names.index(self.desired_class)
            if desired != fact_class:
                return desired

        if len(target_names) == 2:
            return "opposite"
        order = np.argsort(prediction)[::-1]
        return int(order[1])

    def explain_instance(self, instances):
        """Generate counterfactual examples for each instance.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            Dictionary with, for each instance, the model prediction and the
            generated counterfactual examples.
        """
        import numpy as np

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.explainability.model_input import prepare_model_input

        dataset = to_dashai_dataset(instances)
        X = prepare_model_input(self.model, dataset).to_pandas()[self.feature_names]

        predictions = np.asarray(self.model.predict(dataset))

        explanation = {"metadata": self.metadata}
        for i in range(len(X)):
            row = X.iloc[[i]]
            fact_class = int(np.argmax(predictions[i]))
            desired = self._resolve_desired_class(predictions[i], fact_class)

            counterfactuals = []
            try:
                result = self._dice.generate_counterfactuals(
                    row,
                    total_CFs=self.total_cfs,
                    desired_class=desired,
                )
                cfs_frame = result.cf_examples_list[0].final_cfs_df
                if cfs_frame is not None:
                    for _, cf_row in cfs_frame.iterrows():
                        values = [cf_row[f] for f in self.feature_names]
                        changed = [
                            feature
                            for j, feature in enumerate(self.feature_names)
                            if not np.isclose(float(values[j]), float(row.iloc[0, j]))
                        ]
                        counterfactuals.append(
                            {
                                "values": [float(v) for v in values],
                                "predicted_class": int(cf_row[self.output_column]),
                                "changed_features": changed,
                            }
                        )
            except Exception:  # noqa: BLE001 - DiCE may fail to find CFs
                counterfactuals = []

            explanation[i] = {
                "instance_values": row.iloc[0].tolist(),
                "model_prediction": predictions[i].tolist(),
                "predicted_class": fact_class,
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
            predicted_class = instance["predicted_class"]
            predicted_name = target_names[predicted_class]
            counterfactuals = instance["counterfactuals"]

            columns = ["Feature", "Instance"] + [
                f"Counterfactual {k + 1}" for k in range(len(counterfactuals))
            ]
            rows = []
            highlight = []
            for row_idx, feature in enumerate(feature_names):
                row = [feature, instance["instance_values"][row_idx]]
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
        """Describe, in words, the prediction and each counterfactual found.

        Names the predicted class and probability, then lists every
        counterfactual with the features it changed and the class it yields
        (the same values shown in the comparison table from :meth:`plot`).

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
                        "(p={predicted_prob}). DiCE could not generate "
                        "counterfactuals for this instance."
                    ),
                    "es": (
                        "El modelo predijo {predicted_name} "
                        "(p={predicted_prob}). DiCE no pudo generar "
                        "contrafactuales para esta instancia."
                    ),
                    "pt": (
                        "O modelo previu {predicted_name} "
                        "(p={predicted_prob}). O DiCE não conseguiu gerar "
                        "contrafactuais para esta instância."
                    ),
                    "de": (
                        "Das Modell sagte {predicted_name} "
                        "(p={predicted_prob}) voraus. DiCE konnte für diese "
                        "Instanz keine kontrafaktischen Beispiele erzeugen."
                    ),
                    "zh": (
                        "模型预测为{predicted_name}（p={predicted_prob}）。"
                        "DiCE无法为该实例生成反事实样本。"
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
            if changed_features:
                changed = ", ".join(changed_features)
                line = format_story(
                    {
                        "en": (
                            "Counterfactual {n}: changing {changed} yields {cf_name}."
                        ),
                        "es": (
                            "Contrafactual {n}: cambiando {changed} se "
                            "obtiene {cf_name}."
                        ),
                        "pt": (
                            "Contrafactual {n}: alterando {changed} obtém-se {cf_name}."
                        ),
                        "de": (
                            "Kontrafaktisch {n}: Durch Ändern von {changed} "
                            "ergibt sich {cf_name}."
                        ),
                        "zh": "反事实{n}：改变{changed}会得到{cf_name}。",
                    },
                    n=cf_idx + 1,
                    changed=changed,
                    cf_name=cf_name,
                )
            else:
                line = format_story(
                    {
                        "en": (
                            "Counterfactual {n}: changing nothing yields {cf_name}."
                        ),
                        "es": (
                            "Contrafactual {n}: sin cambiar nada se obtiene {cf_name}."
                        ),
                        "pt": (
                            "Contrafactual {n}: sem alterar nada obtém-se {cf_name}."
                        ),
                        "de": (
                            "Kontrafaktisch {n}: Ohne Änderungen ergibt sich {cf_name}."
                        ),
                        "zh": "反事实{n}：不改变任何特征即可得到{cf_name}。",
                    },
                    n=cf_idx + 1,
                    cf_name=cf_name,
                )
            story = concat_stories(story, line, separator="\n")

        return story
