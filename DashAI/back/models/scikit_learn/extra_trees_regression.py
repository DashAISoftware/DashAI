from sklearn.ensemble import ExtraTreesRegressor as _ExtraTreesRegressor

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class ExtraTreesRegressionSchema(BaseSchema):
    """Schema that configures the Extra-Trees Regressor.

    Extra-Trees (Extremely Randomised Trees) builds an ensemble of decision tree
    regressors with fully random feature thresholds, further reducing variance
    compared to Random Forests. The underlying implementation is
    ``sklearn.ensemble.ExtraTreesRegressor``.
    """

    n_estimators: search_space(
        int_field(ge=1),
        fixed=100,
        low=50,
        high=500,
        description=MultilingualString(
            en="The number of trees in the forest.",
            es="El número de árboles en el bosque.",
            pt="O número de árvores na floresta.",
            de="Die Anzahl der Bäume im Wald.",
            zh="森林中的树木数量。",
        ),
        alias=MultilingualString(
            en="N estimators",
            es="N estimadores",
            pt="N estimadores",
            de="Anzahl Schätzer",
            zh="估计器数量",
        ),
    )  # type: ignore

    max_depth: search_space(
        none_type(int_field(ge=1)),
        fixed=None,
        low=1,
        high=32,
        description=MultilingualString(
            en=(
                "The maximum depth of the tree. If None, nodes are expanded until "
                "all leaves are pure or fewer than min_samples_split samples remain."
            ),
            es=(
                "La profundidad máxima del árbol. Si es None, los nodos se expanden "
                "hasta que todas las hojas sean puras o queden menos de "
                "min_samples_split muestras."
            ),
            pt=(
                "A profundidade máxima da árvore. Se None, os nós são expandidos "
                "até que todas as folhas sejam puras ou restem menos de "
                "min_samples_split amostras."
            ),
            de=(
                "Die maximale Tiefe des Baums. Bei None werden Knoten erweitert, bis "
                "alle Blätter rein sind oder weniger als min_samples_split Stichproben "
                "verbleiben."
            ),
            zh=(
                "树的最大深度。若为None，则扩展节点直到所有叶子纯净或"
                "剩余样本数少于min_samples_split。"
            ),
        ),
        alias=MultilingualString(
            en="Max depth",
            es="Profundidad máxima",
            pt="Profundidade máxima",
            de="Maximale Tiefe",
            zh="最大深度",
        ),
    )  # type: ignore

    min_samples_split: search_space(
        int_field(ge=2),
        fixed=2,
        low=2,
        high=10,
        description=MultilingualString(
            en="Minimum number of samples required to split an internal node.",
            es="Número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="Número mínimo de amostras necessárias para dividir um nó interno.",
            de="Mindestanzahl von Stichproben zum Aufteilen eines internen Knotens.",
            zh="拆分内部节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mínimas amostras de divisão",
            de="Minimale Aufteilungsstichproben",
            zh="最小拆分样本数",
        ),
    )  # type: ignore

    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=10,
        description=MultilingualString(
            en="Minimum number of samples required to be at a leaf node.",
            es="Número mínimo de muestras requeridas para estar en una hoja.",
            pt="Número mínimo de amostras necessárias para estar em um nó folha.",
            de="Mindestanzahl von Stichproben an einem Blattknoten.",
            zh="叶节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimas amostras para folha",
            de="Minimale Stichproben für Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore

    bootstrap: search_space(
        bool_field(),
        fixed=False,
        description=MultilingualString(
            en=(
                "Whether bootstrap samples are used when building trees. "
                "If False, the whole dataset is used for each tree."
            ),
            es=(
                "Si se usan muestras bootstrap al construir los árboles. "
                "Si es False, se usa todo el conjunto de datos para cada árbol."
            ),
            pt=(
                "Se amostras bootstrap são usadas ao construir as árvores. "
                "Se False, o conjunto de dados completo é usado para cada árvore."
            ),
            de=(
                "Ob Bootstrap-Stichproben beim Aufbau von Bäumen verwendet werden. "
                "Bei False wird der gesamte Datensatz für jeden Baum verwendet."
            ),
            zh=("构建树时是否使用自助采样。若为False，则每棵树使用完整数据集。"),
        ),
        alias=MultilingualString(
            en="Bootstrap",
            es="Bootstrap",
            pt="Bootstrap",
            de="Bootstrap",
            zh="自助采样",
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
                "或传入None不设置特定种子。"
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


class ExtraTreesRegression(RegressionModel, SklearnLikeRegressor, _ExtraTreesRegressor):
    """Extra-Trees regressor using fully randomised decision tree splits.

    Extremely Randomised Trees pick thresholds at random instead of searching for
    the optimal split, introducing extra randomness that further reduces variance.
    Combined with averaging over many trees, Extra-Trees can achieve very low
    generalisation error on regression tasks while being fast to train.

    Key hyperparameters include ``n_estimators``, ``max_depth``,
    ``min_samples_split``, and ``bootstrap``. The implementation wraps
    scikit-learn's ``ExtraTreesRegressor``.

    References
    ----------
    - [1] Geurts, P., Ernst, D. & Wehenkel, L. (2006). "Extremely randomized trees."
           Machine Learning, 63(1), 3-42.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html
    """

    SCHEMA = ExtraTreesRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Extra-Trees Regression",
        es="Regresión Extra-Trees",
        pt="Regressor de Árvores Extras",
        de="Extra-Trees-Regression",
        zh="极端随机树回归",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Ensemble of fully randomised decision trees for fast, "
            "low-variance regression."
        ),
        es=(
            "Conjunto de árboles de decisión completamente aleatorizados "
            "para regresión rápida y de baja varianza."
        ),
        pt=(
            "Conjunto de árvores de decisão completamente aleatorizadas "
            "para regressão rápida e de baixa variância."
        ),
        de=(
            "Ensemble vollständig zufälliger Entscheidungsbäume für schnelle "
            "Regression mit geringer Varianz."
        ),
        zh="完全随机决策树集成，用于快速低方差回归。",
    )
    COLOR: str = "#26A69A"
    ICON: str = "Park"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
