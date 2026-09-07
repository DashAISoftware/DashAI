from sklearn.neural_network import MLPClassifier as _MLPClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
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


class MLPClassifierSchema(BaseSchema):
    """Schema that configures the MLP Classifier.

    The Multi-layer Perceptron Classifier is a feedforward neural network trained
    with backpropagation. It supports multiple hidden layers and several activation
    functions. The underlying implementation is
    ``sklearn.neural_network.MLPClassifier``.
    """

    hidden_layer_size: search_space(
        int_field(ge=1),
        fixed=100,
        low=10,
        high=500,
        description=MultilingualString(
            en=(
                "Number of neurons in the single hidden layer. The model uses one "
                "hidden layer of this size."
            ),
            es=(
                "Número de neuronas en la capa oculta única. El modelo utiliza una "
                "capa oculta de este tamaño."
            ),
            pt=(
                "Número de neurônios na camada oculta única. O modelo utiliza uma "
                "camada oculta deste tamanho."
            ),
            de=(
                "Anzahl der Neuronen in der einzelnen verdeckten Schicht. Das Modell "
                "verwendet eine verdeckte Schicht dieser Größe."
            ),
            zh="单隐藏层中的神经元数量。模型使用此大小的单隐藏层。",
        ),
        alias=MultilingualString(
            en="Hidden layer size",
            es="Tamaño de capa oculta",
            pt="Tamanho da camada oculta",
            de="Größe der verdeckten Schicht",
            zh="隐藏层大小",
        ),
    )  # type: ignore

    activation: search_space(
        enum_field(enum=["relu", "tanh", "logistic", "identity"]),
        fixed="relu",
        description=MultilingualString(
            en="Activation function for the hidden layer.",
            es="Función de activación para la capa oculta.",
            pt="Função de ativação para a camada oculta.",
            de="Aktivierungsfunktion für die verdeckte Schicht.",
            zh="隐藏层的激活函数。",
        ),
        alias=MultilingualString(
            en="Activation",
            es="Activación",
            pt="Ativação",
            de="Aktivierung",
            zh="激活函数",
        ),
    )  # type: ignore

    solver: search_space(
        enum_field(enum=["adam", "lbfgs", "sgd"]),
        fixed="adam",
        description=MultilingualString(
            en=(
                "The solver for weight optimisation. 'adam' works well for large "
                "datasets; 'lbfgs' converges faster on small datasets; 'sgd' "
                "requires more tuning."
            ),
            es=(
                "El solucionador para la optimización de pesos. 'adam' funciona bien "
                "para datasets grandes; 'lbfgs' converge más rápido en datasets "
                "pequeños; 'sgd' requiere más ajuste."
            ),
            pt=(
                "O solucionador para otimização de pesos. 'adam' funciona bem para "
                "conjuntos de dados grandes; 'lbfgs' converge mais rápido em "
                "conjuntos pequenos; 'sgd' requer mais ajuste."
            ),
            de=(
                "Der Löser für die Gewichtsoptimierung. 'adam' eignet sich für große "
                "Datensätze; 'lbfgs' konvergiert schneller bei kleinen Datensätzen; "
                "'sgd' erfordert mehr Feinabstimmung."
            ),
            zh="权重优化求解器。'adam'适用于大型数据集；'lbfgs'在小型数据集上收敛更快；'sgd'需要更多调参。",
        ),
        alias=MultilingualString(
            en="Solver",
            es="Solucionador",
            pt="Solucionador",
            de="Löser",
            zh="求解器",
        ),
    )  # type: ignore

    alpha: search_space(
        float_field(ge=0.0),
        fixed=0.0001,
        low=1e-06,
        high=1.0,
        description=MultilingualString(
            en="L2 regularisation term (penalty parameter).",
            es="Término de regularización L2 (parámetro de penalización).",
            pt="Termo de regularização L2 (parâmetro de penalidade).",
            de="L2-Regularisierungsterm (Strafparameter).",
            zh="L2正则化项（惩罚参数）。",
        ),
        alias=MultilingualString(
            en="Alpha", es="Alfa", pt="Alfa", de="Alpha", zh="Alpha"
        ),
    )  # type: ignore

    learning_rate_init: search_space(
        float_field(ge=1e-6),
        fixed=0.001,
        low=1e-05,
        high=0.1,
        description=MultilingualString(
            en="The initial learning rate used for weight updates.",
            es="La tasa de aprendizaje inicial usada para actualizar los pesos.",
            pt="A taxa de aprendizado inicial usada para atualizar os pesos.",
            de="Die anfängliche Lernrate für Gewichtsaktualisierungen.",
            zh="用于权重更新的初始学习率。",
        ),
        alias=MultilingualString(
            en="Learning rate init",
            es="Tasa de aprendizaje inicial",
            pt="Taxa de aprendizado inicial",
            de="Anfängliche Lernrate",
            zh="初始学习率",
        ),
    )  # type: ignore

    max_iter: search_space(
        int_field(ge=1),
        fixed=200,
        low=50,
        high=1000,
        description=MultilingualString(
            en=(
                "Maximum number of iterations. The solver iterates until "
                "convergence or this limit."
            ),
            es=(
                "Número máximo de iteraciones. El solucionador itera hasta "
                "convergencia o este límite."
            ),
            pt=(
                "Número máximo de iterações. O solucionador itera até "
                "convergência ou este limite."
            ),
            de=(
                "Maximale Anzahl von Iterationen. Der Löser iteriert bis zur "
                "Konvergenz oder diesem Limit."
            ),
            zh="最大迭代次数。求解器迭代至收敛或达到此上限。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
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
            zh="伪随机数生成器的种子。传入整数以获得可重复输出，或传入None不设置特定种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore


class MLPClassifier(TabularClassificationModel, SklearnLikeClassifier, _MLPClassifier):
    """Multi-layer Perceptron classifier trained with backpropagation.

    MLPClassifier is a fully-connected feedforward neural network. The network
    uses a single hidden layer whose size is controlled by ``hidden_layer_size``.
    Training uses backpropagation with the selected ``solver``. Supports ReLU,
    tanh, logistic, and identity activations.

    Key hyperparameters include ``hidden_layer_size``, ``activation``, ``solver``,
    ``alpha`` (L2 regularisation), ``learning_rate_init``, and ``max_iter``. The
    implementation wraps scikit-learn's ``MLPClassifier``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html
    """

    SCHEMA = MLPClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="MLP Classifier",
        es="Clasificador MLP",
        pt="Classificador MLP",
        de="MLP-Klassifikator",
        zh="多层感知机分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Multi-layer perceptron neural network for tabular classification.",
        es="Red neuronal perceptrón multicapa para clasificación tabular.",
        pt="Rede neural perceptrón multicamada para classificação tabular.",
        de="Mehrschichtiges Perzeptron-Netz für tabellarische Klassifikation.",
        zh="用于表格分类的多层感知机神经网络。",
    )
    COLOR: str = "#EF5350"
    ICON: str = "AccountTree"

    def __init__(self, **kwargs) -> None:
        """Initialise the model, converting hidden_layer_size to a tuple for sklearn.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values; ``hidden_layer_size`` is converted to a tuple
            ``(hidden_layer_size,)`` before being forwarded to sklearn's MLPClassifier.
        """
        hidden_size = kwargs.pop("hidden_layer_size", 100)
        kwargs["hidden_layer_sizes"] = (hidden_size,)
        super().__init__(**kwargs)
