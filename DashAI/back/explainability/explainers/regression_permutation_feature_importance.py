from typing import List, Optional, Union

from DashAI.back.core.artifacts import Artifact, ArtifactGroup, PlotlyArtifact
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.story import concat_stories, format_story
from DashAI.back.models.base_model import BaseModel


class RegressionPermutationFeatureImportanceSchema(BaseSchema):
    """Schema for the regression Permutation Feature Importance explainer.

    Configures the regression scoring metric, the number of permutation
    repeats per feature and the random seed.
    """

    scoring: schema_field(
        enum_field(enum=["r2", "neg_mean_squared_error", "neg_mean_absolute_error"]),
        placeholder="r2",
        description=MultilingualString(
            en=(
                "Regression metric used to evaluate how the model's "
                "performance changes when a particular feature is shuffled."
            ),
            es=(
                "Métrica de regresión utilizada para evaluar cómo cambia el "
                "rendimiento del modelo cuando se baraja una característica."
            ),
            pt=(
                "Métrica de regressão usada para avaliar como o desempenho do "
                "modelo muda quando uma característica é embaralhada."
            ),
            zh="用于评估特定特征被打乱时模型性能变化的回归指标。",
            de=(
                "Regressionsmetrik zur Bewertung, wie sich die Modellleistung "
                "ändert, wenn ein bestimmtes Merkmal permutiert wird."
            ),
        ),
        alias=MultilingualString(
            en="Scoring metric",
            es="Métrica de evaluación",
            pt="Métrica de avaliação",
            zh="评分指标",
            de="Bewertungsmetrik",
        ),
    )  # type: ignore

    n_repeats: schema_field(
        int_field(ge=1),
        placeholder=10,
        description=MultilingualString(
            en="Number of times to permute a feature.",
            es="Número de veces que se permuta una característica.",
            pt="Número de vezes que uma característica é permutada.",
            zh="对特征进行排列的次数。",
            de="Anzahl der Permutationen eines Merkmals.",
        ),
        alias=MultilingualString(
            en="Number of repeats",
            es="Número de repeticiones",
            pt="Número de repetições",
            zh="重复次数",
            de="Anzahl der Wiederholungen",
        ),
    )  # type: ignore

    random_state: schema_field(
        int_field(),
        placeholder=0,
        description=MultilingualString(
            en=(
                "Seed for the random number generator to control permutations "
                "of each feature."
            ),
            es=(
                "Semilla del generador aleatorio para controlar las "
                "permutaciones de cada característica."
            ),
            pt=(
                "Semente do gerador de números aleatórios para controlar as "
                "permutações de cada característica."
            ),
            zh="用于控制每个特征排列的随机数生成器种子。",
            de=(
                "Startwert für den Zufallszahlengenerator zur Steuerung der "
                "Permutationen jedes Merkmals."
            ),
        ),
        alias=MultilingualString(
            en="Random state",
            es="Semilla aleatoria",
            pt="Estado aleatório",
            zh="随机状态",
            de="Zufallszustand",
        ),
    )  # type: ignore

    max_samples_fraction: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=1.0,
        description=MultilingualString(
            en=(
                "Fraction of samples to draw from the test set to calculate "
                "feature importance at each repetition."
            ),
            es=(
                "Fracción de muestras a extraer del conjunto de prueba para "
                "calcular la importancia en cada repetición."
            ),
            pt=(
                "Fração de amostras a extrair do conjunto de teste para "
                "calcular a importância a cada repetição."
            ),
            zh="每次重复时从测试集中抽取的样本比例。",
            de=(
                "Anteil der aus dem Testdatensatz gezogenen Stichproben zur "
                "Berechnung der Merkmalswichtigkeit."
            ),
        ),
        alias=MultilingualString(
            en="Max samples fraction",
            es="Fracción máxima de muestras",
            pt="Fração máxima de amostras",
            zh="最大样本比例",
            de="Maximaler Stichprobenanteil",
        ),
    )  # type: ignore


class RegressionPermutationFeatureImportance(BaseGlobalExplainer):
    """Global permutation feature importance for regression models.

    Measures the importance of each feature by randomly shuffling its values
    across the test set and recording the resulting decrease in a regression
    scoring metric (R2, negative MSE or negative MAE). Repeating the
    permutation ``n_repeats`` times yields a mean importance and standard
    deviation per feature. The method is model agnostic and computed on held
    out data.

    References
    ----------
    - [1] Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
    - [2] Fisher, A. et al. (2019). "All Models are Wrong, but Many are
           Useful." JMLR, 20(177), 1-81. https://arxiv.org/abs/1801.01489
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
    DISPLAY_NAME = MultilingualString(
        en="Permutation Feature Importance (regression)",
        es="Importancia por Permutación (regresión)",
        pt="Importância por Permutação (regressão)",
        zh="排列特征重要性（回归）",
        de="Permutations-Merkmalswichtigkeit (Regression)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Assesses feature importance for regression models by measuring "
            "the drop in a regression metric when a feature's values are "
            "randomly shuffled."
        ),
        es=(
            "Evalúa la importancia de las características en modelos de "
            "regresión midiendo la caída de una métrica de regresión cuando "
            "los valores de una característica se barajan aleatoriamente."
        ),
        pt=(
            "Avalia a importância das características em modelos de regressão "
            "medindo a queda de uma métrica de regressão quando os valores de "
            "uma característica são embaralhados aleatoriamente."
        ),
        zh="通过测量特征值被随机打乱时回归指标的下降来评估回归模型的特征重要性。",
        de=(
            "Bewertet die Merkmalswichtigkeit von Regressionsmodellen durch "
            "Messung des Abfalls einer Regressionsmetrik, wenn die Werte "
            "eines Merkmals zufällig permutiert werden."
        ),
    )
    COLOR = "#3F51B5"
    SCHEMA = RegressionPermutationFeatureImportanceSchema

    def __init__(
        self,
        model: BaseModel,
        scoring: str = "r2",
        n_repeats: int = 10,
        random_state: int = None,
        max_samples_fraction: float = 1.0,
    ):
        """Initialise the regression permutation feature importance explainer.

        Parameters
        ----------
        model : BaseModel
            The trained DashAI regression model to be explained.
        scoring : str
            Regression metric: 'r2', 'neg_mean_squared_error' or
            'neg_mean_absolute_error'.
        n_repeats : int
            Number of times each feature is permuted.
        random_state : int or None
            Seed for the random number generator controlling permutations.
        max_samples_fraction : float
            Fraction of the test set sampled for the calculation.
        """
        super().__init__(model)

        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        metrics = {
            "r2": r2_score,
            "neg_mean_squared_error": lambda y_true, y_pred: (
                -mean_squared_error(y_true, y_pred)
            ),
            "neg_mean_absolute_error": lambda y_true, y_pred: (
                -mean_absolute_error(y_true, y_pred)
            ),
        }

        self.scoring_name = scoring
        self.scoring = metrics[scoring]
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.max_samples_fraction = max_samples_fraction

    def explain(self, dataset):
        """Compute permutation feature importance on the test split.

        Parameters
        ----------
        dataset : Tuple[DatasetDict, DatasetDict]
            A ``(x, y)`` pair where each element has at least a ``"test"``
            split.

        Returns
        -------
        dict
            Dictionary with keys ``"features"``, ``"importances_mean"`` and
            ``"importances_std"``.
        """
        import numpy as np

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = dataset
        # The permuted frames are already in the model feature space, so the
        # model is queried through predict_prepared to skip a second
        # preparation.
        x_test = prepare_model_input(self.model, x["test"]).to_pandas()
        y_test = y["test"].to_pandas().to_numpy().ravel()

        rng = np.random.RandomState(self.random_state)
        n_samples = max(1, int(len(x_test) * self.max_samples_fraction))
        sample_indexes = rng.choice(len(x_test), size=n_samples, replace=False)
        x_sample = x_test.iloc[sample_indexes].reset_index(drop=True)
        y_sample = y_test[sample_indexes]

        baseline_score = self.scoring(
            y_sample, np.asarray(self.model.predict_prepared(x_sample)).ravel()
        )

        results = {"features": [], "importances_mean": [], "importances_std": []}
        for column in x_sample.columns:
            importances = []
            for _ in range(self.n_repeats):
                x_permuted = x_sample.copy()
                x_permuted[column] = x_sample[column].to_numpy()[
                    rng.permutation(n_samples)
                ]
                permuted_score = self.scoring(
                    y_sample,
                    np.asarray(self.model.predict_prepared(x_permuted)).ravel(),
                )
                importances.append(baseline_score - permuted_score)

            results["features"].append(column)
            results["importances_mean"].append(float(np.round(np.mean(importances), 3)))
            results["importances_std"].append(float(np.round(np.std(importances), 3)))

        return results

    def plot(self, explanation: dict) -> List[Artifact]:
        """Create a bar chart of feature importances.

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.

        Returns
        -------
        List[Artifact]
            A list with a single plotly artifact holding the importance bar
            chart.
        """
        import pandas as pd
        import plotly.express as px

        data = pd.DataFrame.from_dict(explanation)
        data = data.sort_values(by=["importances_mean"], ascending=True)

        fig = px.bar(
            data,
            x=data["importances_mean"],
            y=data["features"],
            error_x=data["importances_std"],
        )
        fig.update_layout(
            xaxis_title=f"Importance ({self.scoring_name})",
            yaxis_title=None,
        )

        return [PlotlyArtifact(payload=fig, title="Permutation Feature Importance")]

    def story(
        self, explanation: dict, explainer_output: Union[Artifact, ArtifactGroup]
    ) -> Optional[MultilingualString]:
        """Describe, in words, the ranked feature importances.

        Ranks the features by their mean importance (the same values
        plotted by :meth:`plot`) and names the top-3, calling out when the
        least important of them showed no measurable effect (mean
        importance at or below zero).

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.
        explainer_output : Union[Artifact, ArtifactGroup]
            The artifact previously returned by :meth:`plot`.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not the importance bar chart.
        """
        if isinstance(explainer_output, ArtifactGroup):
            return None

        features = explanation["features"]
        means = explanation["importances_mean"]

        ranking = sorted(
            zip(features, means, strict=True), key=lambda pair: pair[1], reverse=True
        )
        top = ranking[:3]
        positive = [(name, mean) for name, mean in top if mean > 0]
        non_positive = [(name, mean) for name, mean in top if mean <= 0]

        # All top-3 features actually decreased the score when shuffled:
        # "relies most on" the whole ranked list is accurate as-is.
        if not non_positive:
            feature_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in top)
            return format_story(
                {
                    "en": (
                        "Ranked by the drop in {scoring} caused by shuffling "
                        "each feature, the model relies most on: "
                        "{feature_list}."
                    ),
                    "es": (
                        "Ordenadas según la caída en {scoring} al barajar "
                        "cada característica, el modelo depende "
                        "principalmente de: {feature_list}."
                    ),
                    "pt": (
                        "Classificadas pela queda em {scoring} causada ao "
                        "embaralhar cada característica, o modelo depende "
                        "principalmente de: {feature_list}."
                    ),
                    "de": (
                        "Geordnet nach dem Rückgang von {scoring} durch das "
                        "Permutieren jedes Merkmals, verlässt sich das "
                        "Modell hauptsächlich auf: {feature_list}."
                    ),
                    "zh": (
                        "根据打乱各特征后{scoring}的下降程度排序，"
                        "模型主要依赖：{feature_list}。"
                    ),
                },
                scoring=self.scoring_name,
                feature_list=feature_list,
            )

        # None of the top-3 had any measurable effect: saying the model
        # "relies on" them would be backwards.
        if not positive:
            feature_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in top)
            return format_story(
                {
                    "en": (
                        "None of the top 3 features ({feature_list}) showed "
                        "measurable importance when shuffled — that did "
                        "not decrease {scoring}, or even improved it."
                    ),
                    "es": (
                        "Ninguna de las 3 características principales "
                        "({feature_list}) mostró una importancia medible al "
                        "barajarlas — no redujo {scoring}, o incluso lo "
                        "mejoró."
                    ),
                    "pt": (
                        "Nenhuma das 3 características principais "
                        "({feature_list}) mostrou importância mensurável ao "
                        "serem embaralhadas — não reduziu {scoring}, ou até "
                        "o melhorou."
                    ),
                    "de": (
                        "Keines der 3 wichtigsten Merkmale ({feature_list}) "
                        "zeigte beim Permutieren eine messbare Wichtigkeit "
                        "— {scoring} sank dadurch nicht oder verbesserte "
                        "sich sogar."
                    ),
                    "zh": (
                        "打乱后，排名前3的特征（{feature_list}）均未表现出"
                        "可测量的重要性——并未降低{scoring}，甚至有所提升。"
                    ),
                },
                scoring=self.scoring_name,
                feature_list=feature_list,
            )

        # Mixed: only some of the top-3 had a measurable effect — claim
        # reliance on those, and separately note the rest showed none.
        positive_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in positive)
        non_positive_list = ", ".join(name for name, _ in non_positive)
        story = format_story(
            {
                "en": (
                    "Ranked by the drop in {scoring} caused by shuffling "
                    "each feature, the model relies on: {positive_list}."
                ),
                "es": (
                    "Ordenadas según la caída en {scoring} al barajar cada "
                    "característica, el modelo depende de: {positive_list}."
                ),
                "pt": (
                    "Classificadas pela queda em {scoring} causada ao "
                    "embaralhar cada característica, o modelo depende de: "
                    "{positive_list}."
                ),
                "de": (
                    "Geordnet nach dem Rückgang von {scoring} durch das "
                    "Permutieren jedes Merkmals, verlässt sich das Modell "
                    "auf: {positive_list}."
                ),
                "zh": (
                    "根据打乱各特征后{scoring}的下降程度排序，"
                    "模型依赖：{positive_list}。"
                ),
            },
            scoring=self.scoring_name,
            positive_list=positive_list,
        )
        return concat_stories(
            story,
            format_story(
                {
                    "en": (
                        " The remaining features ({non_positive_list}) "
                        "showed no measurable importance when shuffled "
                        "(that did not decrease {scoring}, or even "
                        "improved it)."
                    ),
                    "es": (
                        " Las características restantes "
                        "({non_positive_list}) no mostraron una "
                        "importancia medible al barajarlas (no redujo "
                        "{scoring}, o incluso lo mejoró)."
                    ),
                    "pt": (
                        " As características restantes "
                        "({non_positive_list}) não mostraram importância "
                        "mensurável ao serem embaralhadas (não reduziu "
                        "{scoring}, ou até o melhorou)."
                    ),
                    "de": (
                        " Die übrigen Merkmale ({non_positive_list}) "
                        "zeigten beim Permutieren keine messbare "
                        "Wichtigkeit ({scoring} sank dadurch nicht oder "
                        "verbesserte sich sogar)."
                    ),
                    "zh": (
                        "其余特征（{non_positive_list}）在打乱后没有表现出"
                        "可测量的重要性（并未降低{scoring}，甚至有所"
                        "提升）。"
                    ),
                },
                non_positive_list=non_positive_list,
                scoring=self.scoring_name,
            ),
        )
