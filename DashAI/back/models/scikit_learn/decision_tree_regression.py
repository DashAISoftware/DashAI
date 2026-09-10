from sklearn.tree import DecisionTreeRegressor as _DecisionTreeRegressor

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class DecisionTreeRegressionSchema(BaseSchema):
    """Schema that configures the Decision Tree Regressor.

    The Decision Tree Regressor builds a tree by recursively splitting the feature
    space to minimise MSE (or MAE) at each node. The underlying implementation is
    ``sklearn.tree.DecisionTreeRegressor``.
    """

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
                "A profundidade máxima da árvore. Se None, os nós são expandidos até "
                "que todas as folhas sejam puras ou restem menos de "
                "min_samples_split amostras."
            ),
            de=(
                "Die maximale Tiefe des Baums. Wenn None, werden Knoten erweitert, bis "
                "alle Blätter rein sind oder weniger als min_samples_split Proben übrig"
                "sind."
            ),
            zh=(
                "树的最大深度。若为 None，则节点持续展开，直到所有叶节点纯净或"
                "剩余样本数少于 min_samples_split。"
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
        high=20,
        description=MultilingualString(
            en="Minimum number of samples required to split an internal node.",
            es="Número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="Número mínimo de amostras necessárias para dividir um nó interno.",
            de=(
                "Mindestanzahl an Proben, die zum Aufteilen eines internen Knotens "
                "erforderlich sind."
            ),
            zh="分裂内部节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mínimo de amostras para divisão",
            de="Mindestproben Aufteilung",
            zh="最小分裂样本数",
        ),
    )  # type: ignore

    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=20,
        description=MultilingualString(
            en="Minimum number of samples required to be at a leaf node.",
            es="Número mínimo de muestras requeridas para estar en una hoja.",
            pt="Número mínimo de amostras necessárias para estar em um nó folha.",
            de=(
                "Mindestanzahl an Proben, die in einem Blattknoten vorhanden sein "
                "müssen."
            ),
            zh="叶节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimo de amostras na folha",
            de="Mindestproben Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore

    max_leaf_nodes: search_space(
        none_type(int_field(ge=2)),
        fixed=None,
        low=2,
        high=255,
        description=MultilingualString(
            en=(
                "Grow a tree with at most max_leaf_nodes in best-first fashion. "
                "If None, unlimited leaf nodes."
            ),
            es=(
                "Crecer un árbol con a lo sumo max_leaf_nodes de manera best-first. "
                "Si es None, nodos hoja ilimitados."
            ),
            pt=(
                "Crescer uma árvore com no máximo max_leaf_nodes de forma best-first. "
                "Se None, nós folha ilimitados."
            ),
            de=(
                "Einen Baum mit höchstens max_leaf_nodes Blättern nach "
                "Best-First-Strategie wachsen. "
                "Wenn None, unbegrenzte Blattknoten."
            ),
            zh=(
                "以最优优先方式生长最多 max_leaf_nodes 个叶节点的树。"
                "若为 None，则叶节点数不受限制。"
            ),
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Máximos nodos hoja",
            pt="Máximo de nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore

    min_impurity_decrease: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=0.5,
        description=MultilingualString(
            en=(
                "A node is split if the split induces a decrease of the impurity "
                "greater than or equal to this value."
            ),
            es=(
                "Un nodo se divide si la división induce una disminución de la "
                "impureza mayor o igual a este valor."
            ),
            pt=(
                "Um nó é dividido se a divisão induz uma diminuição da impureza "
                "maior ou igual a este valor."
            ),
            de=(
                "Ein Knoten wird aufgeteilt, wenn die Aufteilung eine Verringerung der "
                "Unreinheit größer oder gleich diesem Wert bewirkt."
            ),
            zh="若分裂导致的不纯度降低量大于或等于该值，则对节点进行分裂。",
        ),
        alias=MultilingualString(
            en="Min impurity decrease",
            es="Disminución mínima de impureza",
            pt="Diminuição mínima de impureza",
            de="Mindest-Unreinheitsverringerung",
            zh="最小不纯度降低",
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
                "Der Startwert des Pseudo-Zufallszahlengenerators. Übergeben Sie eine "
                "ganze Zahl für reproduzierbare Ausgaben oder None für keinen "
                "bestimmten Startwert."
            ),
            zh=(
                "伪随机数生成器的种子。传入整数可获得可复现的输出，"
                "传入 None 则不设置特定种子。"
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


class DecisionTreeRegression(
    RegressionModel, SklearnLikeRegressor, _DecisionTreeRegressor
):
    """Decision tree regressor that recursively partitions the feature space.

    DecisionTreeRegressor builds a binary tree by choosing the split that most
    reduces the MSE (default) at each internal node. Leaf nodes predict the mean
    of the training targets in the region. Decision trees are fast, interpretable,
    and require no feature scaling, but tend to overfit without pruning.

    Key hyperparameters include ``max_depth``, ``min_samples_split``,
    ``min_samples_leaf``, and ``max_leaf_nodes``. The implementation wraps
    scikit-learn's ``DecisionTreeRegressor``.

    References
    ----------
    - [1] Breiman, L. et al. (1984). Classification and Regression Trees. Wadsworth.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html
    """

    SCHEMA = DecisionTreeRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Decision Tree Regression",
        es="Regresión Árbol de Decisión",
        pt="Regressão Árvore de Decisão",
        de="Entscheidungsbaum-Regression",
        zh="决策树回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Interpretable tree based regressor that partitions the feature space.",
        es=(
            "Regresor basado en árbol interpretable que particiona el espacio "
            "de características."
        ),
        pt=(
            "Regressor baseado em árvore interpretável que particiona o espaço "
            "de características."
        ),
        de=(
            "Interpretierbarer baumbasierter Regressor, der den Merkmalsraum "
            "partitioniert."
        ),
        zh="可解释的决策树回归器，对特征空间进行划分。",
    )
    COLOR: str = "#66BB6A"
    ICON: str = "AccountTree"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
