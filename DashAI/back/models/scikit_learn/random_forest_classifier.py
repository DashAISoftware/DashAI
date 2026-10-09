from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifierSchema(BaseSchema):
    """Schema that configures the Random Forest Classifier.

    Random Forest is an ensemble classification algorithm that builds multiple
    decision trees on bootstrap samples of the training data, using a random subset
    of features at each split, and aggregates their predictions by majority vote.
    The underlying implementation is ``sklearn.ensemble.RandomForestClassifier``.
    """

    n_estimators: search_space(
        int_field(ge=1),
        fixed=100,
        low=50,
        high=200,
        description=MultilingualString(
            en=(
                "The 'n_estimators' parameter corresponds to the number of decision "
                "trees. It must be an integer greater than or equal to 1."
            ),
            es=(
                "El parámetro 'n_estimators' corresponde al número de árboles de "
                "decisión. Debe ser un entero mayor o igual a 1."
            ),
            pt=(
                "O parâmetro 'n_estimators' corresponde ao número de árvores de "
                "decisão. Deve ser um inteiro maior ou igual a 1."
            ),
            de=(
                "Der Parameter 'n_estimators' entspricht der Anzahl der "
                "Entscheidungsbäume. "
                "Er muss eine ganze Zahl größer oder gleich 1 sein."
            ),
            zh=("参数'n_estimators'对应决策树的数量，必须为大于或等于1的整数。"),
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
        int_field(ge=1),
        fixed=2,
        low=2,
        high=10,
        description=MultilingualString(
            en=(
                "The parameter corresponds to the maximum depth of the "
                "tree. It must be an integer greater than or equal to 1."
            ),
            es=(
                "El parámetro corresponde a la profundidad máxima del "
                "árbol. Debe ser un entero mayor o igual a 1."
            ),
            pt=(
                "O parâmetro corresponde à profundidade máxima da "
                "árvore. Deve ser um inteiro maior ou igual a 1."
            ),
            de=(
                "Der Parameter entspricht der maximalen Tiefe des Baums. "
                "Er muss eine ganze Zahl größer oder gleich 1 sein."
            ),
            zh="该参数对应树的最大深度，必须为大于或等于1的整数。",
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
            en=(
                "This parameter sets the minimum number of samples "
                "required to split an internal node. It must be a number greater than "
                "or equal to 2."
            ),
            es=(
                "Este parámetro establece el número mínimo de muestras "
                "requeridas para dividir un nodo interno. Debe ser un número mayor o "
                "igual a 2."
            ),
            pt=(
                "Este parâmetro define o número mínimo de amostras "
                "necessárias para dividir um nó interno. Deve ser um número maior ou "
                "igual a 2."
            ),
            de=(
                "Dieser Parameter legt die Mindestanzahl von Stichproben fest, "
                "die zum Aufteilen eines internen Knotens erforderlich sind. "
                "Er muss eine Zahl größer oder gleich 2 sein."
            ),
            zh=("该参数设置拆分内部节点所需的最小样本数，必须为大于或等于2的数。"),
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
            en=(
                "This parameter sets the minimum number of samples "
                "required to be at a leaf node. It must be a number greater than or "
                "equal to 1."
            ),
            es=(
                "Este parámetro establece el número mínimo de muestras "
                "requeridas para estar en una hoja. Debe ser un número mayor o igual "
                "a 1."
            ),
            pt=(
                "Este parâmetro define o número mínimo de amostras "
                "necessárias para estar em um nó folha. Deve ser um número maior ou "
                "igual a 1."
            ),
            de=(
                "Dieser Parameter legt die Mindestanzahl von Stichproben fest, "
                "die an einem Blattknoten erforderlich sind. "
                "Er muss eine Zahl größer oder gleich 1 sein."
            ),
            zh=("该参数设置叶节点所需的最小样本数，必须为大于或等于1的数。"),
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimas amostras para folha",
            de="Minimale Stichproben für Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore
    max_leaf_nodes: search_space(
        int_field(ge=2),
        fixed=2,
        low=2,
        high=10,
        description=MultilingualString(
            en=(
                "This parameter sets the maximum number of leaf nodes. It must be an "
                "integer greater than or equal to 2."
            ),
            es=(
                "Este parámetro establece el número máximo de nodos hoja. Debe ser un "
                "entero mayor o igual a 2."
            ),
            pt=(
                "Este parâmetro define o número máximo de nós folha. Deve ser um "
                "inteiro maior ou igual a 2."
            ),
            de=(
                "Dieser Parameter legt die maximale Anzahl von Blattknoten fest. "
                "Er muss eine ganze Zahl größer oder gleich 2 sein."
            ),
            zh="该参数设置最大叶节点数，必须为大于或等于2的整数。",
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Máximos nodos para hoja",
            pt="Máximos nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=0,
        description=MultilingualString(
            en=("This parameter must be an integer greater than or equal to 0."),
            es=("Este parámetro debe ser un entero mayor o igual a 0."),
            pt=("Este parâmetro deve ser um inteiro maior ou igual a 0."),
            de=("Dieser Parameter muss eine ganze Zahl größer oder gleich 0 sein."),
            zh="该参数必须为大于或等于0的整数。",
        ),
        alias=MultilingualString(
            en="Random State",
            es="Estado Aleatorio",
            pt="Estado Aleatório",
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


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _RandomForestClassifier
):
    """Random forest classifier that aggregates predictions from many decision trees.

    Random Forest is a bagging ensemble that fits ``n_estimators`` decision trees,
    each on a bootstrap sample of the training data. At each split only a random
    subset of features is evaluated, which decorrelates the trees and reduces
    variance. The final class prediction is determined by majority vote across all
    trees.

    Key hyperparameters include ``n_estimators`` (number of trees), ``max_depth``
    (maximum tree depth), ``min_samples_split``, ``min_samples_leaf``,
    ``max_leaf_nodes``, and ``random_state``. The implementation wraps
    scikit-learn's ``RandomForestClassifier``.

    References
    ----------
    - [1] Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
           https://doi.org/10.1023/A:1010933404324
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
    """

    SCHEMA = RandomForestClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Random Forest",
        es="Bosque Aleatorio",
        pt="Classificador de Floresta Aleatória",
        de="Random Forest",
        zh="随机森林",
    )
    DESCRIPTION: str = MultilingualString(
        en="An ensemble learning method using multiple decision trees.",
        es=(
            "Un método de aprendizaje en conjunto que utiliza múltiples árboles de "
            "decisión."
        ),
        pt=(
            "Um método de aprendizado em conjunto que utiliza múltiplas árvores de "
            "decisão."
        ),
        de=("Eine Ensemble-Lernmethode, die mehrere Entscheidungsbäume verwendet."),
        zh="使用多棵决策树的集成学习方法。",
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
