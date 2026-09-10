from sklearn.svm import SVC as _SVC

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
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


class SVCSchema(BaseSchema):
    """Schema that configures the Support Vector Classifier (SVC).

    Support Vector Classification finds the optimal hyperplane that maximises the
    margin between classes in a kernel-transformed feature space. It is used for
    binary and multiclass tabular classification. The underlying implementation is
    ``sklearn.svm.SVC``.
    """

    C: search_space(
        float_field(gt=0.0),
        fixed=1.0,
        low=1.0,
        high=10.0,
        description=MultilingualString(
            en=(
                "The parameter 'C' is a regularization parameter. "
                "The strength of the regularization is inversely proportional to C"
            ),
            es=(
                "El parámetro 'C' es un parámetro de regularización. "
                "La fuerza de la regularización es inversamente proporcional a C"
            ),
            pt=(
                "O parâmetro 'C' é um parâmetro de regularização. "
                "A força da regularização é inversamente proporcional a C"
            ),
            de=(
                "Der Parameter 'C' ist ein Regularisierungsparameter. "
                "Die Stärke der Regularisierung ist umgekehrt proportional zu C."
            ),
            zh="参数'C'是正则化参数，正则化强度与C成反比。",
        ),
        alias=MultilingualString(en="C", es="C", pt="C", de="C", zh="C"),
    )  # type: ignore
    coef0: search_space(
        float_field(),
        fixed=1.0,
        low=1.0,
        high=10.0,
        description=MultilingualString(
            en=(
                "The parameter 'coef0' is independent term in "
                "kernel function. "
                "It is only significant for kernel poly and sigmoid. "
            ),
            es=(
                "El parámetro 'coef0' es un término independiente en la "
                "función del kernel. "
                "Solo es significativo para los kernels poly y sigmoid. "
            ),
            pt=(
                "O parâmetro 'coef0' é um termo independente na "
                "função kernel. "
                "É significativo apenas para kernels poly e sigmoid. "
            ),
            de=(
                "Der Parameter 'coef0' ist ein unabhängiger Term in der "
                "Kernelfunktion. "
                "Er ist nur für die Kernel poly und sigmoid relevant. "
            ),
            zh="参数'coef0'是核函数中的独立项，仅对poly和sigmoid核有意义。",
        ),
        alias=MultilingualString(
            en="coef0", es="coef0", pt="coef0", de="coef0", zh="coef0"
        ),
    )  # type: ignore
    degree: search_space(
        float_field(ge=0.0),
        fixed=1.0,
        low=1.0,
        high=10.0,
        description=MultilingualString(
            en="The 'degree' parameter is only significant for 'poly' kernel.",
            es="El parámetro 'grado' solo es significativo para el kernel 'poly'.",
            pt="O parâmetro 'grau' só é significativo para o kernel 'poly'.",
            de="Der Parameter 'degree' ist nur für den 'poly'-Kernel relevant.",
            zh="参数'degree'仅对'poly'核有意义。",
        ),
        alias=MultilingualString(
            en="degree", es="grado", pt="grau", de="Grad", zh="次数"
        ),
    )  # type: ignore
    gamma: search_space(
        enum_field(enum=["scale", "auto"]),
        fixed="scale",
        description=MultilingualString(
            en="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels.",
            es="Coeficiente para los kernels 'rbf', 'poly' y 'sigmoid'.",
            pt="Coeficiente para kernels 'rbf', 'poly' e 'sigmoid'.",
            de="Koeffizient für 'rbf'-, 'poly'- und 'sigmoid'-Kernel.",
            zh="'rbf'、'poly'和'sigmoid'核的系数。",
        ),
        alias=MultilingualString(
            en="gamma", es="gamma", pt="gamma", de="Gamma", zh="gamma"
        ),
    )  # type: ignore
    kernel: search_space(
        enum_field(enum=["linear", "poly", "rbf", "sigmoid"]),
        fixed="rbf",
        description=MultilingualString(
            en="The 'kernel' parameter is the kernel used in the model.",
            es="El parámetro 'kernel' es el kernel utilizado en el modelo.",
            pt="O parâmetro 'kernel' é o kernel utilizado no modelo.",
            de="Der Parameter 'kernel' gibt den im Modell verwendeten Kernel an.",
            zh="参数'kernel'是模型中使用的核函数。",
        ),
        alias=MultilingualString(
            en="kernel", es="kernel", pt="kernel", de="Kernel", zh="核函数"
        ),
    )  # type: ignore
    max_iter: search_space(
        int_field(ge=-1),
        fixed=-1,
        low=-1,
        high=10,
        description=MultilingualString(
            en=(
                "The 'max_iter' parameter determines the iteration limit for the "
                "solver. It must be of type positive integer "
                "or -1 to indicate no limit."
            ),
            es=(
                "El parámetro 'max_iter' determina el límite de iteraciones para el "
                "solucionador. Debe ser un entero positivo "
                "o -1 para indicar sin límite."
            ),
            pt=(
                "O parâmetro 'max_iter' determina o limite de iterações para o "
                "solucionador. Deve ser um inteiro positivo "
                "ou -1 para indicar sem limite."
            ),
            de=(
                "Der Parameter 'max_iter' bestimmt das Iterationslimit für den "
                "Löser. Muss eine positive ganze Zahl oder "
                "-1 für kein Limit sein."
            ),
            zh="参数'max_iter'确定求解器的最大迭代次数，正整数或-1表示无限制。",
        ),
        alias=MultilingualString(
            en="max iterations",
            es="max iteraciones",
            pt="máx iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    shrinking: search_space(
        bool_field(),
        fixed=True,
        description=MultilingualString(
            en=(
                "The 'shrinking' parameter determines whether "
                "a shrinking heuristic is used."
            ),
            es=(
                "El parámetro 'reducción' determina si "
                "se utiliza una heurística de reducción."
            ),
            pt=(
                "O parâmetro 'redução' determina se "
                "uma heurística de redução é utilizada."
            ),
            de=(
                "Der Parameter 'shrinking' bestimmt, ob "
                "eine Schrumpfungsheuristik verwendet wird."
            ),
            zh="参数'shrinking'决定是否使用收缩启发式方法。",
        ),
        alias=MultilingualString(
            en="shrinking", es="reducción", pt="redução", de="Schrumpfung", zh="收缩"
        ),
    )  # type: ignore
    tol: search_space(
        float_field(gt=0.0),
        fixed=1.0,
        low=1.0,
        high=10.0,
        description=MultilingualString(
            en=("The parameter 'tol' determines the tolerance for the stop criterion."),
            es=(
                "El parámetro 'tol' determina "
                " la tolerancia para el criterio de detención."
            ),
            pt=("O parâmetro 'tol' determina a tolerância para o critério de parada."),
            de="Der Parameter 'tol' bestimmt die Toleranz für das Stoppkriterium.",
            zh="参数'tol'确定停止准则的容差。",
        ),
        alias=MultilingualString(
            en="tolerance", es="tolerancia", pt="tolerância", de="Toleranz", zh="容差"
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


class SVC(TabularClassificationModel, SklearnLikeClassifier, _SVC):
    """Support vector machine classifier that maximises the margin between classes.

    SVC constructs a maximum-margin hyperplane in a (possibly kernel-transformed)
    feature space. Training data points that lie on or inside the margin are called
    support vectors; they fully define the decision boundary. Nonlinearly separable
    problems are addressed by mapping the input space into a higher dimensional space
    via kernel functions (linear, polynomial, RBF, or sigmoid).

    Regularisation is controlled by ``C``: smaller values allow more misclassified
    training points in exchange for a wider margin, while larger values enforce a
    harder margin. The ``kernel``, ``gamma``, ``degree``, and ``coef0`` parameters
    configure the kernel function. The implementation wraps scikit-learn's ``SVC``.

    References
    ----------
    - [1] Cortes, C. & Vapnik, V. (1995). "Support-vector networks."
           Machine Learning, 20(3), 273-297. https://doi.org/10.1007/BF00994018
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
    """

    SCHEMA = SVCSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Support Vector Machine (SVM)",
        es="Máquina de Vectores de Soporte (SVM)",
        pt="Máquina de Vetores de Suporte (SVM)",
        zh="支持向量机（SVM）",
        de="Support-Vektor-Maschine (SVM)",
    )
    DESCRIPTION: str = MultilingualString(
        en="Finds the optimal hyperplane that maximises the margin between classes.",
        es="Encuentra el hiperplano óptimo que maximiza el margen entre clases.",
        pt="Encontra o hiperplano ótimo que maximiza a margem entre classes.",
        zh="寻找最优超平面以最大化类间间隔的分类算法。",
        de="Findet die optimale Hyperebene, die den Margin zwischen Klassen maximiert.",
    )
    COLOR: str = "#FF80AB"
    ICON: str = "Timeline"

    def __init__(self, **kwargs):
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        kwargs["probability"] = True
        super().__init__(**kwargs)
