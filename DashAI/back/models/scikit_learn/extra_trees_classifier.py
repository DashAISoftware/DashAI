from sklearn.ensemble import ExtraTreesClassifier as _ExtraTreesClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    none_type,
    optimizer_int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class ExtraTreesClassifierSchema(BaseSchema):
    """Schema that configures the Extra-Trees Classifier.

    Extra-Trees (Extremely Randomised Trees) builds an ensemble of decision trees
    with fully random feature thresholds, which further reduces variance at the
    cost of a slightly higher bias compared to Random Forests. The underlying
    implementation is ``sklearn.ensemble.ExtraTreesClassifier``.
    """

    n_estimators: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 50,
            "upper_bound": 500,
        },
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

    max_depth: schema_field(
        none_type(optimizer_int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The maximum depth of the tree. If None, nodes are expanded until "
                "all leaves are pure or contain fewer than min_samples_split samples."
            ),
            es=(
                "La profundidad máxima del árbol. Si es None, los nodos se expanden "
                "hasta que todas las hojas sean puras o tengan menos de "
                "min_samples_split muestras."
            ),
            pt=(
                "A profundidade máxima da árvore. Se None, os nós são expandidos "
                "até que todas as folhas sejam puras ou tenham menos de "
                "min_samples_split amostras."
            ),
            de=(
                "Die maximale Tiefe des Baums. Bei None werden Knoten erweitert, bis "
                "alle Blätter rein sind oder weniger als min_samples_split Stichproben "
                "enthalten."
            ),
            zh=(
                "树的最大深度。若为None，则节点持续扩展，直到所有叶节点纯净或"
                "样本数少于min_samples_split。"
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

    min_samples_split: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 10,
        },
        description=MultilingualString(
            en="The minimum number of samples required to split an internal node.",
            es="El número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="O número mínimo de amostras necessárias para dividir um nó interno.",
            de="Mindestanzahl von Stichproben zum Aufteilen eines internen Knotens.",
            zh="拆分内部节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mínimas amostras de divisão",
            de="Minimale Aufteilungsstichproben",
            zh="最小分裂样本数",
        ),
    )  # type: ignore

    min_samples_leaf: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 10,
        },
        description=MultilingualString(
            en="The minimum number of samples required to be at a leaf node.",
            es="El número mínimo de muestras requeridas para estar en una hoja.",
            pt="O número mínimo de amostras necessárias para estar em um nó folha.",
            de="Mindestanzahl von Stichproben an einem Blattknoten.",
            zh="叶节点所需的最少样本数。",
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
            zh=("构建树时是否使用自举采样。若为False，则每棵树使用全部数据集。"),
        ),
        alias=MultilingualString(
            en="Bootstrap",
            es="Bootstrap",
            pt="Bootstrap",
            de="Bootstrap",
            zh="自举采样",
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(optimizer_int_field(ge=0)),
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
                "伪随机数生成器的种子。传入整数以获得可重现的输出，"
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
    class_weight: search_space(
        none_type(enum_field(enum=["balanced", "balanced_subsample"])),
        fixed=None,
        description=MultilingualString(
            en=(
                "Weights associated with classes, used to correct for class "
                "imbalance. 'balanced' adjusts weights inversely proportional to "
                "class frequencies in the whole dataset; 'balanced_subsample' does "
                "the same but per bootstrap sample of each tree. Use None for no "
                "weighting."
            ),
            es=(
                "Pesos asociados a las clases, usados para corregir el desbalance "
                "de clases. 'balanced' ajusta los pesos de forma inversamente "
                "proporcional a la frecuencia de cada clase en todo el conjunto de "
                "datos; 'balanced_subsample' hace lo mismo pero por cada muestra "
                "bootstrap de cada árbol. Use None para no aplicar ponderación."
            ),
            pt=(
                "Pesos associados às classes, usados para corrigir o "
                "desbalanceamento de classes. 'balanced' ajusta os pesos de forma "
                "inversamente proporcional à frequência de cada classe em todo o "
                "conjunto de dados; 'balanced_subsample' faz o mesmo, mas por "
                "amostra bootstrap de cada árvore. Use None para não aplicar "
                "ponderação."
            ),
            de=(
                "Gewichte, die den Klassen zugeordnet sind, um "
                "Klassenungleichgewichte auszugleichen. 'balanced' passt die "
                "Gewichte umgekehrt proportional zur Klassenhäufigkeit im "
                "gesamten Datensatz an; 'balanced_subsample' tut dasselbe, jedoch "
                "pro Bootstrap-Stichprobe jedes Baums. Verwenden Sie None für "
                "keine Gewichtung."
            ),
            zh=(
                "与类别关联的权重，用于纠正类别不平衡。'balanced'根据整个数据集中"
                "各类别频率的反比调整权重；'balanced_subsample'则对每棵树的自举"
                "采样分别执行相同操作。使用None表示不加权。"
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


class ExtraTreesClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _ExtraTreesClassifier
):
    """Extra-Trees classifier using fully randomised decision tree splits.

    Extremely Randomised Trees differ from Random Forests in how splits are chosen:
    instead of searching for the best threshold per feature, Extra-Trees picks
    thresholds at random. This introduces additional randomness that, combined with
    bootstrap aggregation, further reduces variance. Extra-Trees are typically faster
    to train than Random Forests.

    Key hyperparameters include ``n_estimators``, ``max_depth``,
    ``min_samples_split``, ``min_samples_leaf``, and ``bootstrap``. The
    implementation wraps scikit-learn's ``ExtraTreesClassifier``.

    References
    ----------
    - [1] Geurts, P., Ernst, D. & Wehenkel, L. (2006). "Extremely randomized trees."
           Machine Learning, 63(1), 3-42. https://doi.org/10.1007/s10994-006-6226-1
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html
    """

    SCHEMA = ExtraTreesClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Extra-Trees Classifier",
        es="Clasificador Extra-Trees",
        pt="Classificador de Árvores Extras",
        de="Extra-Trees-Klassifikator",
        zh="极端随机树分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Ensemble of fully randomised decision trees for fast, "
            "low-variance classification."
        ),
        es=(
            "Conjunto de árboles de decisión completamente aleatorizados "
            "para clasificación rápida."
        ),
        pt=(
            "Conjunto de árvores de decisão completamente aleatorizadas "
            "para classificação rápida e de baixa variância."
        ),
        de=(
            "Ensemble vollständig zufälliger Entscheidungsbäume für schnelle "
            "Klassifikation mit geringer Varianz."
        ),
        zh="完全随机决策树集成，用于快速低方差分类。",
    )
    COLOR: str = "#66BB6A"
    ICON: str = "Park"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
