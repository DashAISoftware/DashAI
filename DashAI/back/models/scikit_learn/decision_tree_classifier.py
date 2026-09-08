from sklearn.tree import DecisionTreeClassifier as _DecisionTreeClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    search_space,
    union_type,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.model_artifact_mixins import (
    TreeArtifactsMixin,
)
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DecisionTreeClassifierSchema(BaseSchema):
    """Schema that configures the Decision Tree Classifier.

    Decision Trees are a non-parametric supervised classification method that
    recursively partitions the feature space by learning axis-aligned decision rules
    inferred from training data. The tree structure is built using the CART algorithm.
    The underlying implementation is ``sklearn.tree.DecisionTreeClassifier``.
    """

    criterion: search_space(
        enum_field(enum=["entropy", "gini", "log_loss"]),
        fixed="entropy",
        description=MultilingualString(
            en=(
                "The function to measure the quality of a split. Supported criteria "
                'are "gini" for the Gini impurity and "log_loss" and "entropy" both '
                "for the Shannon information gain."
            ),
            es=(
                "La función para medir la calidad de una división. Los criterios "
                'soportados son "gini" para la impureza de Gini y "log_loss" y '
                '"entropy" para la ganancia de información de Shannon.'
            ),
            pt=(
                "A função para medir a qualidade de uma divisão. Os critérios "
                'suportados são "gini" para a impureza de Gini e "log_loss" e '
                '"entropy" para o ganho de informação de Shannon.'
            ),
            de=(
                "Die Funktion zur Messung der Qualität einer Aufteilung. Unterstützte "
                "Kriterien sind 'gini' für die Gini-Unreinheit sowie 'log_loss' und "
                "'entropy' für den Shannon-Informationsgewinn."
            ),
            zh=(
                "衡量分裂质量的函数。支持的准则有：'gini'（基尼不纯度）、"
                "'log_loss' 和 'entropy'（香农信息增益）。"
            ),
        ),
        alias=MultilingualString(
            en="Criterion", es="Criterio", pt="Critério", de="Kriterium", zh="准则"
        ),
    )  # type: ignore
    max_depth: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=10,
        description=MultilingualString(
            en=(
                "The maximum depth of the tree. If None, then nodes are expanded "
                "until all leaves are pure or until all leaves contain less than "
                "min_samples_split samples."
            ),
            es=(
                "La profundidad máxima del árbol. Si es None, los nodos se expanden "
                "hasta que todas las hojas sean puras o hasta que todas las hojas "
                "contengan menos de min_samples_split muestras."
            ),
            pt=(
                "A profundidade máxima da árvore. Se None, os nós são expandidos "
                "até que todas as folhas sejam puras ou até que todas as folhas "
                "contenham menos de min_samples_split amostras."
            ),
            de=(
                "Die maximale Tiefe des Baums. Bei None werden Knoten erweitert, bis "
                "alle Blätter rein sind oder weniger als min_samples_split Stichproben "
                "enthalten."
            ),
            zh=(
                "树的最大深度。若为 None，则扩展节点直至所有叶节点纯净，"
                "或叶节点包含的样本数少于 min_samples_split。"
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
        int_field(ge=1),
        fixed=1,
        low=1,
        high=5,
        description=MultilingualString(
            en="The minimum number of samples required to split an internal node.",
            es="El número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="O número mínimo de amostras necessárias para dividir um nó interno.",
            de="Mindestanzahl von Stichproben zum Aufteilen eines internen Knotens.",
            zh="分裂内部节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mín. amostras de divisão",
            de="Minimale Aufteilungsstichproben",
            zh="最小分裂样本数",
        ),
    )  # type: ignore
    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=5,
        description=MultilingualString(
            en="The minimum number of samples required to be at a leaf node.",
            es="El número mínimo de muestras requeridas para estar en una hoja.",
            pt="O número mínimo de amostras necessárias para estar em uma folha.",
            de="Mindestanzahl von Stichproben an einem Blattknoten.",
            zh="叶节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mín. amostras para folha",
            de="Minimale Stichproben für Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore
    max_features: search_space(
        none_type(
            union_type(enum_field(enum=["sqrt", "log2"]), float_field(gt=0.0, le=1.0))
        ),
        fixed=None,
        description=MultilingualString(
            en=(
                "The number of features to consider when looking for the best split. "
                "If float, then max_features is a percentage of the total number of "
                "features."
            ),
            es=(
                "El número de características a considerar al buscar la mejor "
                "división. Si es float, entonces max_features es un porcentaje del "
                "total de características."
            ),
            pt=(
                "O número de características a considerar ao buscar a melhor divisão. "
                "Se float, max_features é uma porcentagem do total de características."
            ),
            de=(
                "Die Anzahl der Merkmale, die bei der Suche nach der besten Aufteilung "
                "berücksichtigt werden. Als Float ist max_features ein Prozentsatz "
                "der Gesamtzahl der Merkmale."
            ),
            zh=(
                "寻找最佳分裂时考虑的特征数量。若为浮点数，"
                "则 max_features 表示特征总数的百分比。"
            ),
        ),
        alias=MultilingualString(
            en="Max features",
            es="Máximas características",
            pt="Máx. características",
            de="Maximale Merkmale",
            zh="最大特征数",
        ),
    )  # type: ignore
    class_weight: search_space(
        none_type(enum_field(enum=["balanced"])),
        fixed=None,
        description=MultilingualString(
            en=(
                "Weights associated with classes, used to correct for class "
                "imbalance. 'balanced' automatically adjusts weights inversely "
                "proportional to class frequencies. Use None for no weighting."
            ),
            es=(
                "Pesos asociados a las clases, usados para corregir el desbalance "
                "de clases. 'balanced' ajusta automáticamente los pesos de forma "
                "inversamente proporcional a la frecuencia de cada clase. Use None "
                "para no aplicar ponderación."
            ),
            pt=(
                "Pesos associados às classes, usados para corrigir o "
                "desbalanceamento de classes. 'balanced' ajusta automaticamente os "
                "pesos de forma inversamente proporcional à frequência de cada "
                "classe. Use None para não aplicar ponderação."
            ),
            de=(
                "Gewichte, die den Klassen zugeordnet sind, um "
                "Klassenungleichgewichte auszugleichen. 'balanced' passt die "
                "Gewichte automatisch umgekehrt proportional zur "
                "Klassenhäufigkeit an. Verwenden Sie None für keine Gewichtung."
            ),
            zh=(
                "与类别关联的权重，用于纠正类别不平衡。'balanced'会根据类别频率的"
                "反比自动调整权重。使用None表示不加权。"
            ),
        ),
        alias=MultilingualString(
            en="Class weight",
            es="Peso de clase",
            pt="Peso da classe",
            de="Klassengewicht",
            zh="类别权重",
        ),
    )  # type: ignore


class DecisionTreeClassifier(
    TreeArtifactsMixin,
    TabularClassificationModel,
    SklearnLikeClassifier,
    _DecisionTreeClassifier,
):
    """Decision tree classifier that learns axis-aligned decision rules from data.

    A decision tree recursively partitions the feature space into rectangular regions
    by choosing splits that maximise a purity criterion (Gini impurity, entropy, or
    log-loss). At prediction time the tree routes each sample to a leaf node whose
    majority class is returned as the prediction.

    The tree complexity is primarily controlled by ``max_depth``, ``min_samples_split``,
    ``min_samples_leaf``, and ``max_features``. Shallow trees are more interpretable
    but may underfit; very deep trees tend to overfit. The implementation wraps
    scikit-learn's ``DecisionTreeClassifier``, which uses the CART algorithm.

    References
    ----------
    - [1] Breiman, L., Friedman, J., Olshen, R., & Stone, C. (1984).
           "Classification and Regression Trees." Wadsworth.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html
    """

    SCHEMA = DecisionTreeClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Decision Tree",
        es="Árbol de Decisión",
        pt="Árvore de Decisão",
        de="Entscheidungsbaum",
        zh="决策树",
    )
    DESCRIPTION: str = MultilingualString(
        en="Decision tree classifier using CART algorithm.",
        es=("Clasificador de árbol de decisión usando el algoritmo CART."),
        pt="Classificador de árvore de decisão usando o algoritmo CART.",
        de="Entscheidungsbaum-Klassifikator mit dem CART-Algorithmus.",
        zh="使用 CART 算法的决策树分类器。",
    )
    COLOR: str = "#4CAF50"
    ICON: str = "AccountTree"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
