import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class TokenAblationSchema(BaseSchema):
    """Schema for the Token Ablation explainer hyperparameters.

    Configures how many tokens are evaluated per instance and how ablated
    tokens are replaced.
    """

    max_tokens: schema_field(
        int_field(ge=1, le=256),
        placeholder=50,
        description=MultilingualString(
            en=(
                "Maximum number of tokens (whitespace-separated words) "
                "evaluated per instance. Texts longer than this are truncated "
                "for the analysis to bound the number of model calls."
            ),
            es=(
                "Número máximo de tokens (palabras separadas por espacios) "
                "evaluados por instancia. Los textos más largos se truncan "
                "para el análisis para limitar las llamadas al modelo."
            ),
            pt=(
                "Número máximo de tokens (palavras separadas por espaços) "
                "avaliados por instância. Textos mais longos são truncados "
                "para a análise para limitar as chamadas ao modelo."
            ),
            zh="每个实例评估的最大token数（按空格分词）。超长文本将被截断以限制模型调用次数。",
            de=(
                "Maximale Anzahl der pro Instanz ausgewerteten Tokens (durch "
                "Leerzeichen getrennte Wörter). Längere Texte werden für die "
                "Analyse gekürzt, um die Modellaufrufe zu begrenzen."
            ),
        ),
        alias=MultilingualString(
            en="Max tokens",
            es="Máximo de tokens",
            pt="Máximo de tokens",
            zh="最大token数",
            de="Maximale Tokenanzahl",
        ),
    )  # type: ignore

    replacement: schema_field(
        enum_field(enum=["remove", "unk"]),
        placeholder="remove",
        description=MultilingualString(
            en=(
                "How an ablated token is handled: 'remove' deletes it from "
                "the text, 'unk' replaces it with the [UNK] placeholder."
            ),
            es=(
                "Cómo se trata un token eliminado: 'remove' lo borra del "
                "texto, 'unk' lo reemplaza por el marcador [UNK]."
            ),
            pt=(
                "Como um token removido é tratado: 'remove' o exclui do "
                "texto, 'unk' o substitui pelo marcador [UNK]."
            ),
            zh="被消融token的处理方式：'remove'从文本中删除，'unk'替换为[UNK]占位符。",
            de=(
                "Behandlung eines entfernten Tokens: 'remove' löscht es aus "
                "dem Text, 'unk' ersetzt es durch den Platzhalter [UNK]."
            ),
        ),
        alias=MultilingualString(
            en="Replacement strategy",
            es="Estrategia de reemplazo",
            pt="Estratégia de substituição",
            zh="替换策略",
            de="Ersetzungsstrategie",
        ),
    )  # type: ignore


class TokenAblation(BaseLocalExplainer):
    """Occlusion-based local explainer for text classification.

    For each instance, ablates one token at a time (removing it or replacing
    it with an [UNK] placeholder) and measures how much the predicted class
    probability drops. Tokens whose removal causes a large drop are the ones
    the model relied on for its prediction. The method is model agnostic: it
    only queries ``predict``, so it works with any text classifier.

    References
    ----------
    - [1] Zeiler, M.D. & Fergus, R. (2014). "Visualizing and Understanding
           Convolutional Networks." ECCV 2014. https://arxiv.org/abs/1311.2901
    - [2] Li, J. et al. (2016). "Understanding Neural Networks through
           Representation Erasure." https://arxiv.org/abs/1612.08220
    """

    COMPATIBLE_COMPONENTS = ["TextClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Token Ablation",
        es="Ablación de tokens",
        pt="Ablação de tokens",
        zh="Token消融",
        de="Token-Ablation",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Measures each word's importance by removing it from the text "
            "and recording the drop in the predicted class probability."
        ),
        es=(
            "Mide la importancia de cada palabra eliminándola del texto y "
            "registrando la caída en la probabilidad de la clase predicha."
        ),
        pt=(
            "Mede a importância de cada palavra removendo-a do texto e "
            "registrando a queda na probabilidade da classe prevista."
        ),
        zh="通过从文本中删除每个词并记录预测类别概率的下降来衡量词的重要性。",
        de=(
            "Misst die Wichtigkeit jedes Wortes, indem es aus dem Text "
            "entfernt und der Rückgang der vorhergesagten "
            "Klassenwahrscheinlichkeit erfasst wird."
        ),
    )
    COLOR = "#E65100"
    SCHEMA = TokenAblationSchema

    def __init__(
        self,
        model: BaseModel,
        max_tokens: int = 50,
        replacement: str = "remove",
    ) -> None:
        """Initialize a new instance of a TokenAblation explainer.

        Parameters
        ----------
        model : BaseModel
            Text classification model to be explained.
        max_tokens : int
            Maximum number of tokens evaluated per instance.
        replacement : str
            'remove' to delete the token, 'unk' to replace it with [UNK].
        """
        super().__init__(model)
        self.max_tokens = max_tokens
        self.replacement = replacement

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
        TokenAblation
            The fitted explainer instance (``self``).
        """
        _, y = background_dataset
        y_train = y["train"]

        output_column = y_train.column_names[0]
        target_names = y_train.types[output_column].categories
        self.metadata = {"target_names": list(target_names)}

        return self

    def _ablate(self, tokens, index):
        """Build the text variant with the token at ``index`` ablated.

        Parameters
        ----------
        tokens : List[str]
            Whitespace tokens of the original text.
        index : int
            Position of the token to ablate.

        Returns
        -------
        str
            The perturbed text.
        """
        if self.replacement == "unk":
            variant = tokens.copy()
            variant[index] = "[UNK]"
            return " ".join(variant)
        return " ".join(tokens[:index] + tokens[index + 1 :])

    def explain_instance(self, instances):
        """Compute token importances for each instance.

        Parameters
        ----------
        instances : DatasetDict
            Instances to be explained; must contain a single text column.

        Returns
        -------
        dict
            Dictionary with, for each instance, the tokens, their importance
            (probability drop when ablated) and the model prediction.
        """
        import numpy as np
        import pandas as pd

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        dataset = to_dashai_dataset(instances)
        X = dataset.to_pandas()

        # The job may hand over an already-prepared dataset (e.g. tokenized by
        # a transformer model, adding input_ids/attention_mask columns).
        # Rebuild a clean single-text-column dataset so that model.predict can
        # run its own preparation from raw text.
        tokenizer_columns = {"input_ids", "attention_mask", "token_type_ids", "label"}
        text_columns = [c for c in X.columns if c not in tokenizer_columns]
        if not text_columns:
            raise ValueError(f"No text column found among columns: {list(X.columns)}")
        text_column = text_columns[0]
        texts = X[text_column].astype(str).tolist()

        base_dataset = to_dashai_dataset(pd.DataFrame({text_column: texts}))
        base_predictions = np.asarray(self.model.predict(base_dataset))

        explanation = {"metadata": {**self.metadata, "text_column": text_column}}
        for i, text in enumerate(texts):
            tokens = str(text).split()[: self.max_tokens]
            predicted_class = int(np.argmax(base_predictions[i]))
            base_prob = float(base_predictions[i][predicted_class])

            importances = []
            if tokens:
                variants = [self._ablate(tokens, index) for index in range(len(tokens))]
                variants_dataset = to_dashai_dataset(
                    pd.DataFrame({text_column: variants})
                )
                variant_predictions = np.asarray(self.model.predict(variants_dataset))
                importances = [
                    float(
                        np.round(base_prob - variant_predictions[j][predicted_class], 4)
                    )
                    for j in range(len(tokens))
                ]

            explanation[i] = {
                "text": str(text),
                "tokens": tokens,
                "token_importances": importances,
                "model_prediction": base_predictions[i].tolist(),
                "predicted_class": predicted_class,
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each instance as a token importance bar plot.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained instance,
            each holding that instance's token plot.
        """
        import numpy as np
        import pandas as pd
        import plotly.graph_objs as go

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        target_names = metadata["target_names"]
        max_tokens_plotted = 15

        groups = []
        for i in exp:
            instance = exp[i]
            predicted_class = instance["predicted_class"]
            predicted_name = target_names[predicted_class]
            predicted_prob = float(
                np.round(instance["model_prediction"][predicted_class], 3)
            )

            data = pd.DataFrame(
                {
                    "tokens": [
                        f"{token} ({position})"
                        for position, token in enumerate(instance["tokens"])
                    ],
                    "importances": instance["token_importances"],
                }
            )
            data["importance_abs"] = data["importances"].abs()
            data = data.sort_values(by="importance_abs", ascending=True)
            if len(data) > max_tokens_plotted:
                data = data.iloc[-max_tokens_plotted:, :]

            colors = [
                "rgb(231,63,116)" if value >= 0 else "rgb(47,138,196)"
                for value in data["importances"]
            ]
            fig = go.Figure(
                go.Bar(
                    x=data["importances"],
                    y=data["tokens"],
                    orientation="h",
                    marker={"color": colors},
                    text=data["importances"],
                    textposition="auto",
                )
            )
            fig.update_layout(
                title={
                    "text": (
                        f"Token importance for prediction {predicted_name} "
                        f"(p={predicted_prob})"
                    ),
                    "font": {"size": 14},
                },
                margin={"pad": 20, "l": 100, "r": 60, "t": 60, "b": 40},
                xaxis={"title_text": "Probability drop when token is ablated"},
                yaxis={"showgrid": True},
            )

            title = f"Instance {int(i) + 1}"
            plot = PlotlyArtifact(payload=fig)

            groups.append(ArtifactGroup(title=title, artifacts=[plot]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction and most influential tokens.

        Names the predicted class, its probability, and the top-3 tokens by
        absolute importance (the same values plotted by :meth:`plot`).

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

        labeled_tokens = [
            f"{token} ({position})" for position, token in enumerate(instance["tokens"])
        ]
        ranking = sorted(
            zip(labeled_tokens, instance["token_importances"], strict=True),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )
        top = ranking[:3]
        top_tokens = ", ".join(
            f"'{token}' ({importance:+})" for token, importance in top
        )

        return format_story(
            {
                "en": (
                    "The model predicted {predicted_name} "
                    "(p={predicted_prob}). Most influential tokens: "
                    "{top_tokens}."
                ),
                "es": (
                    "El modelo predijo {predicted_name} "
                    "(p={predicted_prob}). Tokens más influyentes: "
                    "{top_tokens}."
                ),
                "pt": (
                    "O modelo previu {predicted_name} "
                    "(p={predicted_prob}). Tokens mais influentes: "
                    "{top_tokens}."
                ),
                "de": (
                    "Das Modell sagte {predicted_name} "
                    "(p={predicted_prob}) voraus. Einflussreichste Tokens: "
                    "{top_tokens}."
                ),
                "zh": (
                    "模型预测为{predicted_name}（p={predicted_prob}）。"
                    "最具影响力的token：{top_tokens}。"
                ),
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
            top_tokens=top_tokens,
        )
