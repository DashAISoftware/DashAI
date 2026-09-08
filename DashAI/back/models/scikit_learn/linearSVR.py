from sklearn.svm import LinearSVR as _LinearSVR

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class LinearSVRSchema(BaseSchema):
    """Schema that configures the Linear Support Vector Regressor (LinearSVR).

    LinearSVR is a support vector regression model that uses a linear kernel. It
    minimises the epsilon-insensitive loss (no penalty for predictions within an
    epsilon-tube around the target) and is particularly efficient on large datasets
    compared to kernel-based SVR. It is used for tabular regression tasks. The
    underlying implementation is ``sklearn.svm.LinearSVR``.
    """

    epsilon: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=1,
        description=MultilingualString(
            en=(
                "Epsilon parameter that specifies the epsilon-tube within "
                "which no penalty is associated."
            ),
            es=(
                "Parámetro epsilon que especifica el tubo-epsilon dentro del cual "
                "no se asocia ninguna penalización."
            ),
            pt=(
                "Parâmetro epsilon que especifica o tubo-epsilon dentro do qual "
                "nenhuma penalidade é associada."
            ),
            de=(
                "Epsilon-Parameter, der den Epsilon-Schlauch angibt, innerhalb "
                "dessen keine Bestrafung angewendet wird."
            ),
            zh="Epsilon参数，指定不关联惩罚的epsilon管范围。",
        ),
        alias=MultilingualString(
            en="Epsilon", es="Epsilon", pt="Épsilon", de="Epsilon", zh="Epsilon"
        ),
    )  # type: ignore

    tol: search_space(
        float_field(ge=0.0),
        fixed=0.0001,
        low=1e-05,
        high=0.1,
        description=MultilingualString(
            en="Tolerance for stopping criterion.",
            es="Tolerancia para el criterio de detención.",
            pt="Tolerância para o critério de parada.",
            de="Toleranz für das Abbruchkriterium.",
            zh="停止准则的容差。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore

    C: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=10,
        description=MultilingualString(
            en=(
                "Regularization parameter. The strength of the regularization "
                "is inversely proportional to C."
            ),
            es=(
                "Parámetro de regularización. La fuerza de la regularización "
                "es inversamente proporcional a C."
            ),
            pt=(
                "Parâmetro de regularização. A força da regularização "
                "é inversamente proporcional a C."
            ),
            de=(
                "Regularisierungsparameter. Die Stärke der Regularisierung "
                "ist umgekehrt proportional zu C."
            ),
            zh="正则化参数，正则化强度与C成反比。",
        ),
        alias=MultilingualString(en="C", es="C", pt="C", de="C", zh="C"),
    )  # type: ignore

    loss: search_space(
        enum_field(enum=["epsilon_insensitive", "squared_epsilon_insensitive"]),
        fixed="epsilon_insensitive",
        description=MultilingualString(
            en=(
                "Specifies the loss function. 'epsilon_insensitive' is "
                "the standard SVR loss."
            ),
            es=(
                "Especifica la función de pérdida. 'epsilon_insensitive' es "
                "la pérdida estándar de SVR."
            ),
            pt=(
                "Especifica a função de perda. 'epsilon_insensitive' é "
                "a perda padrão do SVR."
            ),
            de=(
                "Gibt die Verlustfunktion an. 'epsilon_insensitive' ist "
                "der Standard-SVR-Verlust."
            ),
            zh="指定损失函数，'epsilon_insensitive'为标准SVR损失。",
        ),
        alias=MultilingualString(
            en="Loss", es="Pérdida", pt="Perda", de="Verlust", zh="损失函数"
        ),
    )  # type: ignore

    fit_intercept: search_space(
        bool_field(),
        fixed=True,
        description=MultilingualString(
            en="Whether to calculate the intercept for this model.",
            es="Si se debe calcular el intercepto para este modelo.",
            pt="Se o intercepto deve ser calculado para este modelo.",
            de="Ob der Achsenabschnitt für dieses Modell berechnet werden soll.",
            zh="是否为该模型计算截距。",
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
        ),
    )  # type: ignore

    intercept_scaling: search_space(
        float_field(ge=1.0),
        fixed=1.0,
        low=1.0,
        high=10,
        description=MultilingualString(
            en=(
                "When fit_intercept is True, instance vector x becomes "
                "[x, self.intercept_scaling] in the primal problem."
            ),
            es=(
                "Cuando fit_intercept es True, el vector de instancia x se convierte "
                "en [x, self.intercept_scaling] en el problema primal."
            ),
            pt=(
                "Quando fit_intercept é True, o vetor de instância x se torna "
                "[x, self.intercept_scaling] no problema primal."
            ),
            de=(
                "Wenn fit_intercept True ist, wird der Instanzvektor x zu "
                "[x, self.intercept_scaling] im primalen Problem."
            ),
            zh=(
                "当fit_intercept为True时，实例向量x在原始问题中变为"
                "[x, self.intercept_scaling]。"
            ),
        ),
        alias=MultilingualString(
            en="Intercept scaling",
            es="Escala del intercepto",
            pt="Escala do intercepto",
            de="Achsenabschnitt-Skalierung",
            zh="截距缩放",
        ),
    )  # type: ignore

    dual: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Select the algorithm to either solve the dual or primal "
                "optimization problem."
            ),
            es=(
                "Selecciona el algoritmo para resolver el problema de optimización "
                "dual o primal."
            ),
            pt=(
                "Seleciona o algoritmo para resolver o problema de otimização "
                "dual ou primal."
            ),
            de=(
                "Wählt den Algorithmus zur Lösung des dualen oder primalen "
                "Optimierungsproblems."
            ),
            zh="选择求解对偶或原始优化问题的算法。",
        ),
        alias=MultilingualString(en="Dual", es="Dual", pt="Dual", de="Dual", zh="对偶"),
    )  # type: ignore

    verbose: schema_field(
        int_field(ge=0),
        placeholder=0,
        description=MultilingualString(
            en=(
                "Enable verbose output. Note that this setting takes "
                "advantage of a per-process runtime setting in libsvm."
            ),
            es=(
                "Habilitar salida detallada. Note que esta configuración aprovecha "
                "una configuración de tiempo de ejecución por proceso en libsvm."
            ),
            pt=(
                "Habilitar saída detalhada. Note que esta configuração aproveita "
                "uma configuração de tempo de execução por processo no libsvm."
            ),
            de=(
                "Ausführliche Ausgabe aktivieren. Beachten Sie, dass diese Einstellung "
                "eine prozessweite Laufzeiteinstellung in libsvm nutzt."
            ),
            zh="启用详细输出，该设置利用libsvm中的每进程运行时设置。",
        ),
        alias=MultilingualString(
            en="Verbose", es="Verboso", pt="Verboso", de="Ausführlich", zh="详细输出"
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(int_field(ge=0)),
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
                "Der Seed des Pseudozufallszahlengenerators, der beim "
                "Mischen der Daten verwendet wird."
            ),
            zh="数据混洗时使用的伪随机数生成器种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore

    max_iter: search_space(
        int_field(ge=1),
        fixed=1000,
        low=100,
        high=10000,
        description=MultilingualString(
            en="The maximum number of iterations to be run.",
            es="El número máximo de iteraciones a ejecutar.",
            pt="O número máximo de iterações a executar.",
            de="Die maximale Anzahl der auszuführenden Iterationen.",
            zh="最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore


class LinearSVR(RegressionModel, SklearnLikeRegressor, _LinearSVR):
    """Support vector regression with a linear kernel for large datasets.

    LinearSVR fits a linear function by minimising the epsilon-insensitive loss:
    predictions within ``epsilon`` of the true target incur no penalty, while
    deviations beyond that are penalised linearly. The regularisation parameter
    ``C`` controls the trade-off between margin width and training error. Because it
    uses a linear kernel and relies on liblinear internally, LinearSVR scales to
    large datasets much more efficiently than ``SVR`` with a nonlinear kernel.

    Key hyperparameters include ``C``, ``epsilon``, ``loss`` (epsilon-insensitive or
    squared epsilon-insensitive), ``fit_intercept``, ``dual``, ``tol``, and
    ``max_iter``. The implementation wraps scikit-learn's ``LinearSVR``.

    References
    ----------
    - [1] Fan, R.-E., Chang, K.-W., Hsieh, C.-J., Wang, X.-R., & Lin, C.-J.
           (2008). "LIBLINEAR: A library for large linear classification."
           Journal of Machine Learning Research, 9, 1871-1874.
           https://www.jmlr.org/papers/v9/fan08a.html
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html
    """

    SCHEMA = LinearSVRSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Linear Support Vector Regression",
        es="Regresión de Vectores de Soporte Lineal",
        pt="SVR Linear",
        de="Lineare Stützvektor-Regression",
        zh="线性支持向量回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Support Vector Regression with linear kernel.",
        es="Regresión de Vectores de Soporte con kernel lineal.",
        pt="Regressão de Vetores de Suporte com kernel linear.",
        de="Stützvektor-Regression mit linearem Kernel.",
        zh="使用线性核的支持向量回归。",
    )
    COLOR: str = "#2196F3"
    ICON: str = "Timeline"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
