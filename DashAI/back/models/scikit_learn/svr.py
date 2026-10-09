from sklearn.svm import SVR as _SVR

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class SVRSchema(BaseSchema):
    """Schema that configures the Support Vector Regressor.

    SVR (Support Vector Regression) finds a function that deviates from the
    observed targets by at most ``epsilon`` while being as flat as possible. It
    uses kernel functions to handle nonlinear relationships. The underlying
    implementation is ``sklearn.svm.SVR``.
    """

    kernel: search_space(
        enum_field(enum=["rbf", "linear", "poly", "sigmoid"]),
        fixed="rbf",
        description=MultilingualString(
            en=(
                "Specifies the kernel type to be used in the algorithm. "
                "'rbf' is the default radial basis function."
            ),
            es=(
                "Especifica el tipo de kernel a usar. "
                "'rbf' es la función de base radial predeterminada."
            ),
            pt=(
                "Especifica o tipo de kernel a usar. "
                "'rbf' é a função de base radial padrão."
            ),
            de=(
                "Gibt den Kerneltyp an, der im Algorithmus verwendet wird. "
                "'rbf' ist die standardmäßige radiale Basisfunktion."
            ),
            zh="指定算法中使用的核函数类型。'rbf' 为默认的径向基函数。",
        ),
        alias=MultilingualString(
            en="Kernel", es="Kernel", pt="Kernel", de="Kernel", zh="核函数"
        ),
    )  # type: ignore

    C: search_space(  # noqa: N815
        float_field(ge=1e-4),
        fixed=1.0,
        low=0.01,
        high=100.0,
        description=MultilingualString(
            en=(
                "Regularisation parameter. Inversely proportional to the "
                "strength of the regularisation."
            ),
            es=(
                "Parámetro de regularización. Inversamente proporcional a la "
                "fuerza de la regularización."
            ),
            pt=(
                "Parâmetro de regularização. Inversamente proporcional à "
                "força da regularização."
            ),
            de=(
                "Regularisierungsparameter. Umgekehrt proportional zur "
                "Stärke der Regularisierung."
            ),
            zh="正则化参数，与正则化强度成反比。",
        ),
        alias=MultilingualString(en="C", es="C", pt="C", de="C", zh="C"),
    )  # type: ignore

    epsilon: search_space(
        float_field(ge=0.0),
        fixed=0.1,
        low=0.0,
        high=1.0,
        description=MultilingualString(
            en=(
                "Specifies the epsilon-tube within which no penalty is associated "
                "in the training loss function."
            ),
            es=(
                "Especifica el tubo epsilon dentro del cual no se asocia penalización "
                "en la función de pérdida de entrenamiento."
            ),
            pt=(
                "Especifica o tubo epsilon dentro do qual nenhuma penalização é "
                "associada na função de perda de treinamento."
            ),
            de=(
                "Gibt den Epsilon-Schlauch an, innerhalb dessen keine Bestrafung "
                "in der Trainings-Verlustfunktion angewendet wird."
            ),
            zh="指定训练损失函数中不施加惩罚的 epsilon 不敏感管范围。",
        ),
        alias=MultilingualString(
            en="Epsilon", es="Épsilon", pt="Épsilon", de="Epsilon", zh="Epsilon"
        ),
    )  # type: ignore

    gamma: search_space(
        enum_field(enum=["scale", "auto"]),
        fixed="scale",
        description=MultilingualString(
            en=(
                "Kernel coefficient for 'rbf', 'poly' and 'sigmoid'. "
                "'scale' uses 1/(n_features * X.var()); 'auto' uses 1/n_features."
            ),
            es=(
                "Coeficiente del kernel para 'rbf', 'poly' y 'sigmoid'. "
                "'scale' usa 1/(n_features * X.var()); 'auto' usa 1/n_features."
            ),
            pt=(
                "Coeficiente do kernel para 'rbf', 'poly' e 'sigmoid'. "
                "'scale' usa 1/(n_features * X.var()); 'auto' usa 1/n_features."
            ),
            de=(
                "Kernel-Koeffizient für 'rbf', 'poly' und 'sigmoid'. "
                "'scale' verwendet 1/(n_features * X.var()); 'auto' verwendet "
                "1/n_features."
            ),
            zh=(
                "'rbf'、'poly' 和 'sigmoid' 的核系数。"
                "'scale' 使用 1/(n_features * X.var())；'auto' 使用 1/n_features。"
            ),
        ),
        alias=MultilingualString(
            en="Gamma", es="Gamma", pt="Gamma", de="Gamma", zh="Gamma"
        ),
    )  # type: ignore

    max_iter: search_space(
        int_field(ge=-1),
        fixed=-1,
        low=100,
        high=10000,
        description=MultilingualString(
            en=("Hard limit on iterations within solver. -1 means no limit."),
            es=(
                "Límite en iteraciones dentro del solucionador. "
                "-1 significa sin límite."
            ),
            pt=("Limite de iterações dentro do solucionador. -1 significa sem limite."),
            de=("Maximale Iterationen im Löser. -1 bedeutet kein Limit."),
            zh="求解器迭代次数的硬性上限，-1 表示无限制。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Iterações máximas",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore


class SVR(RegressionModel, SklearnLikeRegressor, _SVR):
    """Support Vector Regressor using kernel-based function estimation.

    SVR seeks a function that deviates from the targets by at most ``epsilon``
    (the insensitive tube) while maintaining flatness (controlled by ``C``).
    Kernel functions allow SVR to capture nonlinear relationships. The RBF kernel
    is effective in many practical scenarios.

    Key hyperparameters include ``kernel``, ``C``, ``epsilon``, ``gamma``, and
    ``max_iter``. The implementation wraps scikit-learn's ``SVR``.

    References
    ----------
    - [1] Vapnik, V.N. (1995). The Nature of Statistical Learning Theory. Springer.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
    """

    SCHEMA = SVRSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Support Vector Regression",
        es="Regresión de Vectores de Soporte",
        pt="Regressão de Vetores de Suporte",
        de="Stützvektor-Regression",
        zh="支持向量回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Kernel-based SVR that finds a function within an epsilon-insensitive tube.",
        es=(
            "SVR basado en kernel que encuentra una función dentro de un tubo "
            "insensible a épsilon."
        ),
        pt=(
            "SVR baseado em kernel que encontra uma função dentro de um tubo "
            "insensível a épsilon."
        ),
        de=(
            "Kernelbasierter SVR, der eine Funktion innerhalb eines "
            "Epsilon-unempfindlichen Schlauchs findet."
        ),
        zh="基于核函数的支持向量回归，在 epsilon 不敏感管内寻找拟合函数。",
    )
    COLOR: str = "#EF5350"
    ICON: str = "ControlPoint"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
