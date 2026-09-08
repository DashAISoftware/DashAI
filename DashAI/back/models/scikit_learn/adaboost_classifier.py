from sklearn.ensemble import AdaBoostClassifier as _AdaBoostClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
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


class AdaBoostClassifierSchema(BaseSchema):
    """Schema that configures the AdaBoost Classifier.

    AdaBoost (Adaptive Boosting) fits a sequence of weak learners on repeatedly
    re-weighted versions of the training data. Misclassified samples receive
    increased weight so that subsequent learners focus on harder examples. The
    underlying implementation is ``sklearn.ensemble.AdaBoostClassifier``.
    """

    n_estimators: search_space(
        int_field(ge=1),
        fixed=50,
        low=10,
        high=500,
        description=MultilingualString(
            en=(
                "The maximum number of estimators at which boosting is terminated. "
                "In case of perfect fit, the learning procedure is stopped early."
            ),
            es=(
                "El número máximo de estimadores en el que se termina el boosting. "
                "En caso de ajuste perfecto, el procedimiento de aprendizaje se "
                "detiene antes."
            ),
            pt=(
                "O número máximo de estimadores em que o boosting é encerrado. "
                "Em caso de ajuste perfeito, o procedimento de aprendizado é "
                "interrompido antes."
            ),
            de=(
                "Die maximale Anzahl von Schätzern, bei der das Boosting beendet wird. "
                "Bei perfekter Anpassung wird das Lernverfahren vorzeitig gestoppt."
            ),
            zh=("终止提升的最大估计器数量。若出现完美拟合，学习过程将提前停止。"),
        ),
        alias=MultilingualString(
            en="N estimators",
            es="N estimadores",
            pt="N estimadores",
            de="Anzahl Schätzer",
            zh="估计器数量",
        ),
    )  # type: ignore

    learning_rate: search_space(
        float_field(ge=0.01),
        fixed=1.0,
        low=0.01,
        high=2.0,
        description=MultilingualString(
            en=(
                "Weight applied to each classifier at each boosting iteration. "
                "A higher learning rate increases the contribution of each classifier."
            ),
            es=(
                "Peso aplicado a cada clasificador en cada iteración de boosting. "
                "Una tasa de aprendizaje mayor incrementa la contribución de cada "
                "clasificador."
            ),
            pt=(
                "Peso aplicado a cada classificador em cada iteração de boosting. "
                "Uma taxa de aprendizado maior aumenta a contribuição de cada "
                "classificador."
            ),
            de=(
                "Gewicht für jeden Klassifikator bei jeder Boosting-Iteration. "
                "Eine höhere Lernrate erhöht den Beitrag jedes Klassifikators."
            ),
            zh=(
                "每次提升迭代中施加给每个分类器的权重。学习率越高，每个分类器的贡献越大。"
            ),
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
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
                "伪随机数生成器的种子。传入整数以获得可复现的输出，"
                "或传入 None 以不设置特定种子。"
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


class AdaBoostClassifier(
    TreeEnsembleArtifactsMixin,
    TabularClassificationModel,
    SklearnLikeClassifier,
    _AdaBoostClassifier,
):
    """AdaBoost classifier that adapts to misclassified samples iteratively.

    AdaBoost fits a sequence of weak classifiers (decision stumps by default) on
    re-weighted training data, giving more weight to misclassified examples at each
    round. The final prediction is a weighted majority vote of all weak classifiers.
    AdaBoost is sensitive to noisy data and outliers.

    Key hyperparameters include ``n_estimators``, ``learning_rate``, and
    ``random_state``. The implementation wraps scikit-learn's
    ``AdaBoostClassifier``.

    References
    ----------
    - [1] Freund, Y. & Schapire, R.E. (1997). "A Decision-Theoretic Generalization
           of On-Line Learning and an Application to Boosting." Journal of Computer
           and System Sciences, 55(1), 119-139.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.AdaBoostClassifier.html
    """

    SCHEMA = AdaBoostClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="AdaBoost Classifier",
        es="Clasificador AdaBoost",
        pt="Classificador AdaBoost",
        de="AdaBoost-Klassifikator",
        zh="AdaBoost 分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Adaptive boosting that focuses on misclassified samples.",
        es="Boosting adaptivo que se enfoca en muestras mal clasificadas.",
        pt=(
            "Boosting adaptivo que se concentra em amostras classificadas "
            "incorretamente."
        ),
        de=(
            "Adaptives Boosting, das sich auf falsch klassifizierte Stichproben "
            "konzentriert."
        ),
        zh="自适应提升算法，专注于被误分类的样本。",
    )
    COLOR: str = "#FFA726"
    ICON: str = "Bolt"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
