from sklearn.ensemble import BaggingClassifier as _BaggingClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.model_artifact_mixins import (
    TreeEnsembleArtifactsMixin,
)
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class BaggingClassifierSchema(BaseSchema):
    """Schema that configures the Bagging Classifier.

    Bagging (Bootstrap Aggregating) fits base classifiers on random subsets of the
    training data (drawn with replacement) and aggregates their predictions by
    majority vote. It reduces variance and helps avoid overfitting. The underlying
    implementation is ``sklearn.ensemble.BaggingClassifier``.
    """

    n_estimators: search_space(
        int_field(ge=1),
        fixed=10,
        low=5,
        high=100,
        description=MultilingualString(
            en="The number of base estimators in the ensemble.",
            es="El número de estimadores base en el conjunto.",
            pt="O número de estimadores base no conjunto.",
            de="Die Anzahl der Basis-Schätzer im Ensemble.",
            zh="集成中基础估计器的数量。",
        ),
        alias=MultilingualString(
            en="N estimators",
            es="N estimadores",
            pt="N estimadores",
            de="Anzahl Schätzer",
            zh="估计器数量",
        ),
    )  # type: ignore

    max_samples: search_space(
        float_field(gt=0.0, le=1.0),
        fixed=1.0,
        low=0.1,
        high=1.0,
        description=MultilingualString(
            en=(
                "Fraction of training samples drawn for each base estimator "
                "(0 < max_samples ≤ 1.0)."
            ),
            es=(
                "Fracción de muestras de entrenamiento para cada estimador base "
                "(0 < max_samples ≤ 1.0)."
            ),
            pt=(
                "Fração de amostras de treinamento para cada estimador base "
                "(0 < max_samples ≤ 1.0)."
            ),
            de=(
                "Anteil der Trainingsstichproben für jeden Basis-Schätzer "
                "(0 < max_samples ≤ 1.0)."
            ),
            zh="每个基础估计器抽取的训练样本比例（0 < max_samples ≤ 1.0）。",
        ),
        alias=MultilingualString(
            en="Max samples",
            es="Máximas muestras",
            pt="Máximo de amostras",
            de="Maximale Stichproben",
            zh="最大样本数",
        ),
    )  # type: ignore

    max_features: search_space(
        float_field(gt=0.0, le=1.0),
        fixed=1.0,
        low=0.1,
        high=1.0,
        description=MultilingualString(
            en=(
                "Fraction of features drawn for each base estimator "
                "(0 < max_features ≤ 1.0)."
            ),
            es=(
                "Fracción de características para cada estimador base "
                "(0 < max_features ≤ 1.0)."
            ),
            pt=(
                "Fração de características para cada estimador base "
                "(0 < max_features ≤ 1.0)."
            ),
            de=(
                "Anteil der Merkmale für jeden Basis-Schätzer (0 < max_features ≤ 1.0)."
            ),
            zh="每个基础估计器抽取的特征比例（0 < max_features ≤ 1.0）。",
        ),
        alias=MultilingualString(
            en="Max features",
            es="Máximas características",
            pt="Máximo de características",
            de="Maximale Merkmale",
            zh="最大特征数",
        ),
    )  # type: ignore

    bootstrap: search_space(
        bool_field(),
        fixed=True,
        description=MultilingualString(
            en="Whether to draw samples with replacement.",
            es="Si se extraen muestras con reemplazo.",
            pt="Se as amostras são extraídas com reposição.",
            de="Ob Stichproben mit Zurücklegen gezogen werden.",
            zh="是否有放回地抽取样本。",
        ),
        alias=MultilingualString(
            en="Bootstrap", es="Bootstrap", pt="Bootstrap", de="Bootstrap", zh="自助法"
        ),
    )  # type: ignore

    bootstrap_features: search_space(
        bool_field(),
        fixed=False,
        description=MultilingualString(
            en="Whether to draw features with replacement.",
            es="Si se extraen características con reemplazo.",
            pt="Se as características são extraídas com reposição.",
            de="Ob Merkmale mit Zurücklegen gezogen werden.",
            zh="是否有放回地抽取特征。",
        ),
        alias=MultilingualString(
            en="Bootstrap features",
            es="Bootstrap características",
            pt="Bootstrap características",
            de="Bootstrap-Merkmale",
            zh="自助法特征",
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(int_field(ge=0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The seed of the pseudo-random number generator. Pass an int for "
                "reproducible output, or None to not set a specific seed."
            ),
            es=(
                "La semilla del generador de números pseudoaleatorios. Pase un int "
                "para salida reproducible, o None para no fijar una semilla."
            ),
            pt=(
                "A semente do gerador de números pseudoaleatórios. Passe um int para "
                "saída reproduzível, ou None para não definir uma semente específica."
            ),
            de=(
                "Der Seed des Pseudozufallszahlengenerators. Übergeben Sie eine ganze "
                "Zahl für "
                "reproduzierbare Ausgaben oder None, um keinen bestimmten Seed "
                "festzulegen."
            ),
            zh=(
                "伪随机数生成器的种子。传入整数以获得可复现的结果，"
                "或传入 None 不设置特定种子。"
            ),
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore


class BaggingClassifier(
    TreeEnsembleArtifactsMixin,
    TabularClassificationModel,
    SklearnLikeClassifier,
    _BaggingClassifier,
):
    """Bagging classifier that aggregates predictions from bootstrap subsets.

    Bagging builds multiple base classifiers, each trained on a bootstrap sample of
    the training data. The final class prediction is determined by majority voting.
    Bagging is particularly effective with high-variance, low-bias estimators such
    as decision trees.

    Key hyperparameters include ``n_estimators``, ``max_samples``,
    ``max_features``, and ``bootstrap``. The implementation wraps scikit-learn's
    ``BaggingClassifier``.

    References
    ----------
    - [1] Breiman, L. (1996). "Bagging Predictors." Machine Learning, 24(2), 123-140.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.BaggingClassifier.html
    """

    SCHEMA = BaggingClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Bagging Classifier",
        es="Clasificador Bagging",
        pt="Classificador Bagging",
        de="Bagging-Klassifikator",
        zh="Bagging 分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Bootstrap aggregating ensemble to reduce variance.",
        es="Conjunto de bootstrap aggregating para reducir la varianza.",
        pt="Conjunto de bootstrap aggregating para reduzir a variância.",
        de="Bagging-Ensemble zur Varianzreduktion.",
        zh="自助聚合集成方法，用于降低模型方差。",
    )
    COLOR: str = "#26C6DA"
    ICON: str = "Inventory"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
