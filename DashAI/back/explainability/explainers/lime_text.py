import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class LimeTextSchema(BaseSchema):
    """Schema for the LIME text explainer hyperparameters.

    Configures how many words are reported and how many perturbed samples
    LIME draws to fit its local surrogate model.
    """

    num_features: schema_field(
        int_field(ge=1, le=50),
        placeholder=10,
        description=MultilingualString(
            en="Maximum number of words reported in the explanation.",
            es="Número máximo de palabras reportadas en la explicación.",
            pt="Número máximo de palavras reportadas na explicação.",
            zh="解释中报告的最大词数。",
            de="Maximale Anzahl der in der Erklärung gemeldeten Wörter.",
        ),
        alias=MultilingualString(
            en="Number of words",
            es="Número de palabras",
            pt="Número de palavras",
            zh="词数",
            de="Anzahl der Wörter",
        ),
    )  # type: ignore

    num_samples: schema_field(
        int_field(ge=100, le=5000),
        placeholder=1000,
        description=MultilingualString(
            en=(
                "Number of perturbed texts sampled to fit the local surrogate "
                "model. More samples give more stable explanations but take "
                "longer."
            ),
            es=(
                "Número de textos perturbados muestreados para ajustar el "
                "modelo sustituto local. Más muestras dan explicaciones más "
                "estables pero tardan más."
            ),
            pt=(
                "Número de textos perturbados amostrados para ajustar o "
                "modelo substituto local. Mais amostras dão explicações mais "
                "estáveis, mas demoram mais."
            ),
            zh="为拟合局部代理模型而采样的扰动文本数量。样本越多解释越稳定，但耗时越长。",
            de=(
                "Anzahl der gestörten Texte zum Anpassen des lokalen "
                "Ersatzmodells. Mehr Stichproben ergeben stabilere "
                "Erklärungen, dauern aber länger."
            ),
        ),
        alias=MultilingualString(
            en="Number of samples",
            es="Número de muestras",
            pt="Número de amostras",
            zh="样本数量",
            de="Anzahl der Stichproben",
        ),
    )  # type: ignore


class LimeText(BaseLocalExplainer):
    """LIME explanations for text classification models.

    Fits a sparse linear surrogate model on random word-masked variants of
    the input text, weighting variants by similarity to the original. The
    surrogate's coefficients estimate each word's contribution to the
    predicted class. Model agnostic: only ``predict`` is queried. Compared to
    Token Ablation (one word at a time), LIME captures joint effects of
    removing several words but is stochastic and needs more model calls.

    References
    ----------
    - [1] Ribeiro, M.T., Singh, S. & Guestrin, C. (2016). "'Why Should I
           Trust You?' Explaining the Predictions of Any Classifier."
           KDD 2016. https://arxiv.org/abs/1602.04938
    - [2] https://github.com/marcotcr/lime
    """

    COMPATIBLE_COMPONENTS = ["TextClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="LIME (text)",
        es="LIME (texto)",
        pt="LIME (texto)",
        zh="LIME（文本）",
        de="LIME (Text)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Fits a local linear surrogate on word-masked text variants to "
            "estimate each word's contribution to the prediction."
        ),
        es=(
            "Ajusta un sustituto lineal local sobre variantes del texto con "
            "palabras enmascaradas para estimar la contribución de cada "
            "palabra a la predicción."
        ),
        pt=(
            "Ajusta um substituto linear local em variantes do texto com "
            "palavras mascaradas para estimar a contribuição de cada palavra "
            "à previsão."
        ),
        zh="在词遮蔽的文本变体上拟合局部线性代理模型，以估计每个词对预测的贡献。",
        de=(
            "Passt ein lokales lineares Ersatzmodell auf wortmaskierten "
            "Textvarianten an, um den Beitrag jedes Wortes zur Vorhersage zu "
            "schätzen."
        ),
    )
    COLOR = "#2E7D32"
    SCHEMA = LimeTextSchema

    def __init__(
        self,
        model: BaseModel,
        num_features: int = 10,
        num_samples: int = 1000,
    ) -> None:
        """Initialize a new instance of a LimeText explainer.

        Parameters
        ----------
        model : BaseModel
            Text classification model to be explained.
        num_features : int
            Maximum number of words reported per explanation.
        num_samples : int
            Number of perturbed texts sampled by LIME.
        """
        super().__init__(model)
        self.num_features = num_features
        self.num_samples = num_samples

    def fit(self, background_dataset, **kwargs):
        """Store class names from the training targets.

        Parameters
        ----------
        background_dataset : Tuple[DatasetDict, DatasetDict]
            Tuple ``(x, y)`` with the dataset splits.
        **kwargs : Any
            Ignored; present for interface compatibility.

        Returns
        -------
        LimeText
            The fitted explainer instance (``self``).
        """
        _, y = background_dataset
        y_train = y["train"]

        output_column = y_train.column_names[0]
        target_names = y_train.types[output_column].categories
        self.metadata = {"target_names": [str(c) for c in target_names]}

        return self

    def explain_instance(self, instances):
        """Compute LIME word attributions for each instance.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained; must contain a single text column
            (tokenizer artifact columns are ignored).

        Returns
        -------
        dict
            Dictionary with, for each instance, the word weights and the
            model prediction.
        """
        import numpy as np
        import pandas as pd
        from lime.lime_text import LimeTextExplainer

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        dataset = to_dashai_dataset(instances)
        X = dataset.to_pandas()

        # Same guard as TokenAblation: the job may hand over a dataset the
        # model already prepared (tokenized), so rebuild from raw text only.
        tokenizer_columns = {"input_ids", "attention_mask", "token_type_ids", "label"}
        text_columns = [c for c in X.columns if c not in tokenizer_columns]
        if not text_columns:
            raise ValueError(f"No text column found among columns: {list(X.columns)}")
        text_column = text_columns[0]
        texts = X[text_column].astype(str).tolist()

        def classifier_fn(variant_texts):
            variants_dataset = to_dashai_dataset(
                pd.DataFrame({text_column: list(variant_texts)})
            )
            return np.asarray(self.model.predict(variants_dataset))

        base_dataset = to_dashai_dataset(pd.DataFrame({text_column: texts}))
        base_predictions = np.asarray(self.model.predict(base_dataset))

        target_names = self.metadata["target_names"]
        lime_explainer = LimeTextExplainer(class_names=target_names, random_state=0)

        explanation = {"metadata": {**self.metadata, "text_column": text_column}}
        for i, text in enumerate(texts):
            predicted_class = int(np.argmax(base_predictions[i]))

            lime_result = lime_explainer.explain_instance(
                text,
                classifier_fn,
                labels=(predicted_class,),
                num_features=self.num_features,
                num_samples=self.num_samples,
            )
            word_weights = [
                [word, float(np.round(weight, 4))]
                for word, weight in lime_result.as_list(label=predicted_class)
            ]

            explanation[i] = {
                "text": text,
                "word_weights": word_weights,
                "model_prediction": base_predictions[i].tolist(),
                "predicted_class": predicted_class,
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each instance as a word weight bar plot.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained instance,
            each holding that instance's word weight plot.
        """
        import numpy as np
        import plotly.graph_objs as go

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        target_names = metadata["target_names"]

        groups = []
        for i in exp:
            instance = exp[i]
            predicted_class = instance["predicted_class"]
            predicted_name = target_names[predicted_class]
            predicted_prob = float(
                np.round(instance["model_prediction"][predicted_class], 3)
            )
            word_weights = sorted(
                instance["word_weights"], key=lambda pair: abs(pair[1])
            )

            words = [pair[0] for pair in word_weights]
            weights = [pair[1] for pair in word_weights]
            colors = [
                "rgb(231,63,116)" if value >= 0 else "rgb(47,138,196)"
                for value in weights
            ]
            fig = go.Figure(
                go.Bar(
                    x=weights,
                    y=words,
                    orientation="h",
                    marker={"color": colors},
                    text=weights,
                    textposition="auto",
                )
            )
            fig.update_layout(
                title={
                    "text": (
                        f"LIME word weights for {predicted_name} (p={predicted_prob})"
                    ),
                    "font": {"size": 14},
                },
                margin={"pad": 20, "l": 100, "r": 60, "t": 60, "b": 40},
                xaxis={"title_text": "Weight (towards predicted class)"},
                yaxis={"showgrid": True},
            )

            title = f"Instance {int(i) + 1}"
            plot = PlotlyArtifact(payload=fig)

            groups.append(ArtifactGroup(title=title, artifacts=[plot]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction and most influential words.

        Names the predicted class, its probability, and the top-3 words by
        absolute LIME weight (the same values plotted by :meth:`plot`).

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

        target_names = explanation["metadata"]["target_names"]
        instance = explanation[index]

        predicted_class = instance["predicted_class"]
        predicted_name = target_names[predicted_class]
        predicted_prob = round(instance["model_prediction"][predicted_class], 3)

        top = sorted(
            instance["word_weights"], key=lambda pair: abs(pair[1]), reverse=True
        )[:3]
        top_words = ", ".join(f"'{word}' ({weight:+})" for word, weight in top)

        return format_story(
            {
                "en": (
                    "The model predicted {predicted_name} "
                    "(p={predicted_prob}). Most influential words: "
                    "{top_words}."
                ),
                "es": (
                    "El modelo predijo {predicted_name} "
                    "(p={predicted_prob}). Palabras más influyentes: "
                    "{top_words}."
                ),
                "pt": (
                    "O modelo previu {predicted_name} "
                    "(p={predicted_prob}). Palavras mais influentes: "
                    "{top_words}."
                ),
                "de": (
                    "Das Modell sagte {predicted_name} "
                    "(p={predicted_prob}) voraus. Einflussreichste Wörter: "
                    "{top_words}."
                ),
                "zh": (
                    "模型预测为{predicted_name}（p={predicted_prob}）。"
                    "最具影响力的词：{top_words}。"
                ),
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
            top_words=top_words,
        )
