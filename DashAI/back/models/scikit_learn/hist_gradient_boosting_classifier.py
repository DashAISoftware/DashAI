from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifierSchema(BaseSchema):
    """Schema that configures the Histogram-based Gradient Boosting Classifier.

    Histogram-based Gradient Boosting is a fast sequential ensemble classification
    method that bins continuous features into histograms before building each tree,
    greatly reducing the computational cost on large datasets. It is inspired by
    LightGBM and natively handles missing values. The underlying implementation is
    ``sklearn.ensemble.HistGradientBoostingClassifier``.
    """

    learning_rate: search_space(
        float_field(ge=0.0),
        fixed=0.1,
        low=0.1,
        high=1,
        description=MultilingualString(
            en=(
                "The learning rate, also known as shrinkage. This is used as a "
                "multiplicative factor for the leaves values. Use 1 for no shrinkage."
            ),
            es=(
                "La tasa de aprendizaje, también conocida como shrinkage. Se utiliza "
                "como factor multiplicativo para los valores de las hojas. Use 1 para "
                "no aplicar shrinkage."
            ),
            pt=(
                "A taxa de aprendizado, também conhecida como encolhimento. É usada "
                "como fator multiplicativo para os valores das folhas. Use 1 para "
                "não aplicar encolhimento."
            ),
            de=(
                "Die Lernrate, auch als Schrumpfung bekannt. Wird als multiplikativer "
                "Faktor für Blattwerte verwendet. Verwenden Sie 1 für keine "
                "Schrumpfung."
            ),
            zh="学习率，也称为收缩率。用作叶节点值的乘法因子。使用1表示不收缩。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore
    max_iter: search_space(
        int_field(ge=0),
        fixed=100,
        low=100,
        high=250,
        description=MultilingualString(
            en=(
                "The maximum number of iterations of the boosting process, i.e. the "
                "maximum number of trees for binary classification."
            ),
            es=(
                "El número máximo de iteraciones del proceso de boosting, es decir, "
                "el número máximo de árboles para clasificación binaria."
            ),
            pt=(
                "O número máximo de iterações do processo de boosting, ou seja, "
                "o número máximo de árvores para classificação binária."
            ),
            de=(
                "Die maximale Anzahl von Iterationen des Boosting-Prozesses, d.h. die "
                "maximale Anzahl von Bäumen für binäre Klassifikation."
            ),
            zh="提升过程的最大迭代次数，即二元分类的最大树数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    max_depth: search_space(
        int_field(ge=0),
        fixed=1,
        low=1,
        high=10,
        description=MultilingualString(
            en=(
                "The maximum depth of each tree. The depth of a tree is the number "
                "of edges to go from the root to the deepest leaf. Depth isn't "
                "constrained by default."
            ),
            es=(
                "La profundidad máxima de cada árbol. La profundidad es el número de "
                "aristas desde la raíz hasta la hoja más profunda. Por defecto, la "
                "profundidad no está restringida."
            ),
            pt=(
                "A profundidade máxima de cada árvore. A profundidade é o número de "
                "arestas da raiz até a folha mais profunda. Por padrão, a "
                "profundidade não é restringida."
            ),
            de=(
                "Die maximale Tiefe jedes Baums. Die Tiefe ist die Anzahl der Kanten "
                "von der Wurzel bis zum tiefsten Blatt. Standardmäßig nicht begrenzt."
            ),
            zh="每棵树的最大深度。深度是从根节点到最深叶节点的边数。默认不限制深度。",
        ),
        alias=MultilingualString(
            en="Max depth",
            es="Profundidad máxima",
            pt="Profundidade máxima",
            de="Maximale Tiefe",
            zh="最大深度",
        ),
    )  # type: ignore
    max_leaf_nodes: search_space(
        int_field(ge=2),
        fixed=31,
        low=10,
        high=40,
        description=MultilingualString(
            en=(
                "The maximum number of leaves for each tree. Must be strictly "
                "greater than 1. If None, there is no maximum limit."
            ),
            es=(
                "El número máximo de hojas para cada árbol. Debe ser estrictamente "
                "mayor que 1. Si es None, no hay límite máximo."
            ),
            pt=(
                "O número máximo de folhas para cada árvore. Deve ser estritamente "
                "maior que 1. Se None, não há limite máximo."
            ),
            de=(
                "Die maximale Anzahl von Blättern für jeden Baum. Muss strikt "
                "größer als 1 sein. Bei None gibt es kein Maximum."
            ),
            zh="每棵树的最大叶节点数。必须严格大于1。若为None则无上限。",
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Nodos de hoja máximos",
            pt="Máximos nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore
    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=20,
        low=2,
        high=25,
        description=MultilingualString(
            en="The minimum number of samples required to be at a leaf node.",
            es="El número mínimo de muestras requeridas para estar en una hoja.",
            pt="O número mínimo de amostras necessárias para estar em um nó folha.",
            de=(
                "Die Mindestanzahl von Stichproben, die an einem Blattknoten "
                "erforderlich sind."
            ),
            zh="叶节点所需的最小样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Muestras de hoja mínimas",
            pt="Mínimas amostras para folha",
            de="Minimale Stichproben für Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore
    l2_regularization: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=1.0,
        description=MultilingualString(
            en="The L2 regularization parameter. Use 0 for no regularization.",
            es=(
                "El parámetro de regularización L2. "
                "Use 0 para no aplicar regularización."
            ),
            pt=(
                "O parâmetro de regularização L2. Use 0 para não aplicar regularização."
            ),
            de=(
                "Der L2-Regularisierungsparameter. Verwenden Sie 0 für keine "
                "Regularisierung."
            ),
            zh="L2正则化参数。使用0表示不正则化。",
        ),
        alias=MultilingualString(
            en="L2 regularization",
            es="Regularización L2",
            pt="Regularização L2",
            de="L2-Regularisierung",
            zh="L2正则化",
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


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _HistGradientBoostingClassifier
):
    """Histogram-based gradient boosting classifier for large datasets.

    This classifier is a gradient boosting variant that discretises features into
    integer-valued bins (histograms) before tree construction. The histogram
    representation reduces both the number of candidate split points and the memory
    footprint, allowing efficient training on datasets with tens of thousands of
    samples or more. The algorithm natively supports missing values and categorical
    features. It is inspired by the LightGBM algorithm.

    Key hyperparameters include ``learning_rate``, ``max_iter`` (number of boosting
    stages), ``max_depth``, ``max_leaf_nodes``, ``min_samples_leaf``, and
    ``l2_regularization``. The implementation wraps scikit-learn's
    ``HistGradientBoostingClassifier``.

    References
    ----------
    - [1] Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting
           Decision Tree." Advances in Neural Information Processing Systems 30.
           https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html
    """

    SCHEMA = HistGradientBoostingClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Histogram-based Gradient Boosting",
        es="Gradient Boosting basado en histogramas",
        pt="Classificador por Gradient Boosting Histogramado",
        de="Histogramm-basiertes Gradient Boosting",
        zh="基于直方图的梯度提升",
    )
    DESCRIPTION: str = MultilingualString(
        en="Fast gradient boosting using histogram-based algorithms.",
        es=("Gradient boosting rápido usando algoritmos basados en histogramas."),
        pt=("Gradient boosting rápido usando algoritmos baseados em histogramas."),
        de=("Schnelles Gradient Boosting mit histogrammbasierten Algorithmen."),
        zh="使用基于直方图算法的快速梯度提升分类器。",
    )
    COLOR: str = "#9575CD"
    ICON: str = "RocketLaunch"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
