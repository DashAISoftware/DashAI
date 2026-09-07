from sklearn.ensemble import RandomForestRegressor as _RandomForestRegressor

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
    search_space,
    union_type,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RandomForestRegressionSchema(BaseSchema):
    """Schema that configures the Random Forest Regressor.

    Random Forest is an ensemble regression algorithm that builds multiple decision
    trees on bootstrap samples of the training data, using a random subset of
    features at each split, and averages their predictions to produce the final
    output. The underlying implementation is
    ``sklearn.ensemble.RandomForestRegressor``.
    """

    n_estimators: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 10,
            "upper_bound": 1000,
        },
        description=MultilingualString(
            en="The number of trees in the forest.",
            es="El número de árboles en el bosque.",
            pt="O número de árvores na floresta.",
            de="Die Anzahl der Bäume im Wald.",
            zh="森林中树的数量。",
        ),
        alias=MultilingualString(
            en="N estimators",
            es="N estimadores",
            pt="N estimadores",
            de="Anzahl Schätzer",
            zh="估计器数量",
        ),
    )  # type: ignore

    criterion: search_space(
        enum_field(enum=["squared_error", "absolute_error", "poisson"]),
        fixed="squared_error",
        description=MultilingualString(
            en="The function to measure the quality of a split.",
            es="La función para medir la calidad de una división.",
            pt="A função para medir a qualidade de uma divisão.",
            de="Die Funktion zur Messung der Qualität einer Aufteilung.",
            zh="衡量分割质量的函数。",
        ),
        alias=MultilingualString(
            en="Criterion", es="Criterio", pt="Critério", de="Kriterium", zh="标准"
        ),
    )  # type: ignore

    max_depth: schema_field(
        none_type(optimizer_int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en="The maximum depth of the tree.",
            es="La profundidad máxima del árbol.",
            pt="A profundidade máxima da árvore.",
            de="Die maximale Tiefe des Baums.",
            zh="树的最大深度。",
        ),
        alias=MultilingualString(
            en="Max depth",
            es="Profundidad máxima",
            pt="Profundidade máxima",
            de="Maximale Tiefe",
            zh="最大深度",
        ),
    )  # type: ignore

    min_samples_split: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 20,
        },
        description=MultilingualString(
            en="The minimum number of samples required to split an internal node.",
            es="El número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="O número mínimo de amostras necessárias para dividir um nó interno.",
            de=(
                "Mindestanzahl an Proben, die zum Aufteilen eines internen Knotens "
                "erforderlich sind."
            ),
            zh="分割内部节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mínimas amostras de divisão",
            de="Mindestproben Aufteilung",
            zh="最小分割样本数",
        ),
    )  # type: ignore

    min_samples_leaf: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 20,
        },
        description=MultilingualString(
            en="The minimum number of samples required to be at a leaf node.",
            es="El número mínimo de muestras requeridas para estar en una hoja.",
            pt="O número mínimo de amostras necessárias para estar em um nó folha.",
            de=(
                "Mindestanzahl an Proben, die in einem Blattknoten vorhanden sein "
                "müssen."
            ),
            zh="叶节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimas amostras para folha",
            de="Mindestproben Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore

    min_weight_fraction_leaf: schema_field(
        float_field(ge=0.0, le=0.5),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "The minimum weighted fraction of the sum total of weights "
                "required to be at a leaf node."
            ),
            es=(
                "La fracción ponderada mínima de la suma total de pesos "
                "requerida para estar en una hoja."
            ),
            pt=(
                "A fração ponderada mínima da soma total de pesos "
                "necessária para estar em um nó folha."
            ),
            de=(
                "Der minimale gewichtete Anteil der Gesamtgewichte, "
                "der in einem Blattknoten vorhanden sein muss."
            ),
            zh="叶节点所需权重总和的最小加权比例。",
        ),
        alias=MultilingualString(
            en="Min weight fraction leaf",
            es="Fracción de peso mínima para hoja",
            pt="Fração mínima de peso para folha",
            de="Mindestgewichtsanteil Blatt",
            zh="最小权重比例叶节点",
        ),
    )  # type: ignore

    max_features: search_space(
        # "auto" was deprecated in scikit-learn 1.1 and removed in 1.3, and it
        # was the first option in the list, so it is the one a user trying the
        # dropdown reached first. None moves out of the enum because enum_field
        # is str-typed and could never validate it.
        none_type(
            union_type(
                optimizer_float_field(gt=0.0, le=1.0),
                enum_field(enum=["sqrt", "log2"]),
            )
        ),
        fixed="sqrt",
        description=MultilingualString(
            en=("The number of features to consider when looking for the best split."),
            es=(
                "El número de características a considerar al buscar la mejor división."
            ),
            pt=("O número de características a considerar ao buscar a melhor divisão."),
            de=(
                "Die Anzahl der Merkmale, die bei der Suche nach der besten Aufteilung "
                "berücksichtigt werden."
            ),
            zh="寻找最佳分割时考虑的特征数量。",
        ),
        alias=MultilingualString(
            en="Max features",
            es="Máximas características",
            pt="Máximo de características",
            de="Maximale Merkmale",
            zh="最大特征数",
        ),
    )  # type: ignore

    max_leaf_nodes: schema_field(
        none_type(optimizer_int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en="Grow trees with max_leaf_nodes in best-first fashion.",
            es="Crecer árboles con max_leaf_nodes de manera best-first.",
            pt="Crescer árvores com max_leaf_nodes de maneira melhor-primeiro.",
            de="Bäume mit max_leaf_nodes Blättern nach Best-First-Strategie wachsen.",
            zh="以最优先方式生长具有max_leaf_nodes的树。",
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Máximos nodos hoja",
            pt="Máximos nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore

    min_impurity_decrease: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "A node will be split if this split induces a decrease of "
                "the impurity greater than or equal to this value."
            ),
            es=(
                "Un nodo se dividirá si esta división induce una disminución de "
                "la impureza mayor o igual a este valor."
            ),
            pt=(
                "Um nó será dividido se esta divisão induzir uma diminuição da "
                "impureza maior ou igual a este valor."
            ),
            de=(
                "Ein Knoten wird aufgeteilt, wenn diese Aufteilung eine Verringerung "
                "der Unreinheit größer oder gleich diesem Wert bewirkt."
            ),
            zh="若分割导致不纯度下降大于等于此值，则分割节点。",
        ),
        alias=MultilingualString(
            en="Min impurity decrease",
            es="Disminución mínima de impureza",
            pt="Diminuição mínima de impureza",
            de="Mindest-Unreinheitsverringerung",
            zh="最小不纯度下降",
        ),
    )  # type: ignore

    bootstrap: search_space(
        bool_field(),
        fixed=True,
        description=MultilingualString(
            en="Whether bootstrap samples are used when building trees.",
            es="Si se usan muestras bootstrap al construir árboles.",
            pt="Se amostras bootstrap são usadas ao construir árvores.",
            de="Ob Bootstrap-Proben beim Erstellen von Bäumen verwendet werden.",
            zh="构建树时是否使用自助法采样。",
        ),
        alias=MultilingualString(
            en="Bootstrap", es="Bootstrap", pt="Bootstrap", de="Bootstrap", zh="自助法"
        ),
    )  # type: ignore

    oob_score: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "Whether to use out of bag samples to estimate the "
                "generalization score."
            ),
            es=(
                "Si se usan muestras out-of-bag para estimar "
                "la puntuación de generalización."
            ),
            pt=(
                "Se amostras out-of-bag são usadas para estimar "
                "a pontuação de generalização."
            ),
            de=(
                "Ob Out-of-Bag-Proben zur Schätzung des Generalisierungswerts verwendet"
                "werden."
            ),
            zh="是否使用袋外样本估计泛化得分。",
        ),
        alias=MultilingualString(
            en="OOB score",
            es="Puntuación OOB",
            pt="Pontuação OOB",
            de="OOB-Wertung",
            zh="OOB得分",
        ),
    )  # type: ignore

    n_jobs: schema_field(
        none_type(optimizer_int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en="The number of jobs to run in parallel for both fit and predict.",
            es="El número de trabajos a ejecutar en paralelo para fit y predict.",
            pt="O número de tarefas a executar em paralelo para fit e predict.",
            de="Die Anzahl der parallel auszuführenden Jobs für Fit und Vorhersage.",
            zh="拟合和预测时并行运行的作业数。",
        ),
        alias=MultilingualString(
            en="N jobs", es="N trabajos", pt="N tarefas", de="Anzahl Jobs", zh="作业数"
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(optimizer_int_field(ge=0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The seed of the pseudo-random number generator to use "
                "when shuffling the data."
            ),
            es=(
                "La semilla del generador de números pseudoaleatorios a usar "
                "al mezclar los datos."
            ),
            pt=(
                "A semente do gerador de números pseudoaleatórios a usar "
                "ao embaralhar os dados."
            ),
            de=(
                "Der Startwert des Pseudo-Zufallszahlengenerators beim Mischen der "
                "Daten."
            ),
            zh="打乱数据时使用的伪随机数生成器种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore

    warm_start: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "When set to True, reuse the solution of the previous "
                "call to fit and add more estimators to the ensemble."
            ),
            es=(
                "Cuando se establece en True, reutiliza la solución de la llamada "
                "anterior a fit y agrega más estimadores al conjunto."
            ),
            pt=(
                "Quando definido como True, reutiliza a solução da chamada anterior "
                "a fit e adiciona mais estimadores ao conjunto."
            ),
            de=(
                "Wenn True, wird die Lösung des vorherigen Aufrufs wiederverwendet "
                "und dem Ensemble weitere Schätzer hinzugefügt."
            ),
            zh="设为True时，复用上次fit的解并向集成中添加更多估计器。",
        ),
        alias=MultilingualString(
            en="Warm start",
            es="Inicio en caliente",
            pt="Início a quente",
            de="Warmstart",
            zh="热启动",
        ),
    )  # type: ignore

    ccp_alpha: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 1.0,
        },
        description=MultilingualString(
            en="Complexity parameter used for Minimal Cost-Complexity Pruning.",
            es="Parámetro de complejidad usado para poda de costo-complejidad mínima.",
            pt=(
                "Parâmetro de complexidade usado para poda de "
                "custo-complexidade mínima."
            ),
            de="Komplexitätsparameter für das minimale Kosten-Komplexitätsbeschneiden.",
            zh="用于最小代价复杂度剪枝的复杂度参数。",
        ),
        alias=MultilingualString(
            en="CCP alpha", es="CCP alfa", pt="CCP alfa", de="CCP Alpha", zh="CCP alpha"
        ),
    )  # type: ignore

    max_samples: schema_field(
        none_type(optimizer_float_field(gt=0.0, le=1.0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "If bootstrap is True, the number of samples to draw from "
                "X to train each base estimator."
            ),
            es=(
                "Si bootstrap es True, el número de muestras a tomar de "
                "X para entrenar cada estimador base."
            ),
            pt=(
                "Se bootstrap é True, o número de amostras a extrair de "
                "X para treinar cada estimador base."
            ),
            de=(
                "Wenn Bootstrap True ist, die Anzahl der aus X zu ziehenden Proben "
                "zum Trainieren jedes Basis-Schätzers."
            ),
            zh="若bootstrap为True，从X中抽取用于训练每个基估计器的样本数。",
        ),
        alias=MultilingualString(
            en="Max samples",
            es="Máximas muestras",
            pt="Máximas amostras",
            de="Maximale Proben",
            zh="最大样本数",
        ),
    )  # type: ignore


class RandomForestRegression(
    RegressionModel, SklearnLikeRegressor, _RandomForestRegressor
):
    """Random forest regressor that averages predictions from multiple decision trees.

    Random Forest is a bagging ensemble that fits ``n_estimators`` decision trees,
    each on a bootstrap sample of the training data. At each split only a random
    subset of features is considered, decorrelating the trees and reducing variance
    relative to a single tree. The final prediction is the mean of all individual
    tree predictions.

    Key hyperparameters include ``n_estimators``, ``criterion``, ``max_depth``,
    ``min_samples_split``, ``min_samples_leaf``, ``max_features``, ``bootstrap``,
    and ``random_state``. The implementation wraps scikit-learn's
    ``RandomForestRegressor``.

    References
    ----------
    - [1] Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
           https://doi.org/10.1023/A:1010933404324
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
    """

    SCHEMA = RandomForestRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Random Forest",
        es="Bosque Aleatorio",
        pt="Regressor de Floresta Aleatória",
        de="Random-Forest-Regression",
        zh="随机森林回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="An ensemble learning method using multiple decision trees for regression.",
        es=(
            "Un método de aprendizaje en conjunto usando múltiples árboles de "
            "decisión para regresión."
        ),
        pt=(
            "Um método de aprendizado em conjunto usando múltiplas árvores de "
            "decisão para regressão."
        ),
        de=(
            "Eine Ensemble-Lernmethode, die mehrere Entscheidungsbäume für die "
            "Regression kombiniert."
        ),
        zh="使用多棵决策树进行回归的集成学习方法。",
    )
    COLOR: str = "#FF8A65"
    ICON: str = "Forest"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
