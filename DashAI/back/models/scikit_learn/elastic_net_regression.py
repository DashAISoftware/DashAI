from sklearn.linear_model import ElasticNet as _ElasticNet

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class ElasticNetRegressionSchema(BaseSchema):
    """Schema that configures the Elastic Net Regression model.

    Elastic Net combines L1 and L2 penalties, inheriting Lasso's sparse solutions
    and Ridge's grouping effect. The ``l1_ratio`` controls the balance between
    both penalties. The underlying implementation is
    ``sklearn.linear_model.ElasticNet``.
    """

    alpha: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.0001,
            "upper_bound": 10.0,
        },
        description=MultilingualString(
            en=(
                "Regularisation strength multiplier. alpha=0 is OLS; "
                "increasing alpha increases regularisation."
            ),
            es=(
                "Multiplicador de fuerza de regularización. alpha=0 es MCO; "
                "aumentar alpha incrementa la regularización."
            ),
            pt=(
                "Multiplicador da força de regularização. alpha=0 é OLS; "
                "aumentar alpha aumenta a regularização."
            ),
            de=(
                "Regularisierungsstärke-Multiplikator. alpha=0 entspricht OLS; "
                "größere Werte erhöhen die Regularisierung."
            ),
            zh="正则化强度乘数。alpha=0 等同于 OLS；增大 alpha 会增强正则化。",
        ),
        alias=MultilingualString(
            en="Alpha", es="Alfa", pt="Alfa", de="Alpha", zh="Alpha"
        ),
    )  # type: ignore

    l1_ratio: schema_field(
        optimizer_float_field(ge=0.0, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.5,
            "lower_bound": 0.0,
            "upper_bound": 1.0,
        },
        description=MultilingualString(
            en=(
                "The mixing parameter. l1_ratio=0 is pure Ridge; "
                "l1_ratio=1 is pure Lasso."
            ),
            es=(
                "El parámetro de mezcla. l1_ratio=0 es Ridge puro; "
                "l1_ratio=1 es Lasso puro."
            ),
            pt=(
                "O parâmetro de mistura. l1_ratio=0 é Ridge puro; "
                "l1_ratio=1 é Lasso puro."
            ),
            de=(
                "Der Mischungsparameter. l1_ratio=0 ist reines Ridge; "
                "l1_ratio=1 ist reines Lasso."
            ),
            zh="混合参数。l1_ratio=0 为纯 Ridge；l1_ratio=1 为纯 Lasso。",
        ),
        alias=MultilingualString(
            en="L1 ratio",
            es="Ratio L1",
            pt="Razão L1",
            de="L1-Verhältnis",
            zh="L1 比率",
        ),
    )  # type: ignore

    fit_intercept: search_space(
        bool_field(),
        fixed=True,
        description=MultilingualString(
            en=(
                "Whether to calculate the intercept for this model. If False, "
                "the data is expected to be already centred."
            ),
            es=(
                "Si se calcula el intercepto para este modelo. Si es False, "
                "se espera que los datos ya estén centrados."
            ),
            pt=(
                "Se o intercepto deve ser calculado para este modelo. Se False, "
                "espera-se que os dados já estejam centrados."
            ),
            de=(
                "Ob der Achsenabschnitt für dieses Modell berechnet werden soll. Bei "
                "False "
                "wird erwartet, dass die Daten bereits zentriert sind."
            ),
            zh="是否为模型计算截距。若为 False，则假定数据已中心化。",
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
        ),
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=100),
        placeholder={
            "optimize": False,
            "fixed_value": 1000,
            "lower_bound": 100,
            "upper_bound": 10000,
        },
        description=MultilingualString(
            en="The maximum number of iterations.",
            es="El número máximo de iteraciones.",
            pt="O número máximo de iterações.",
            de="Die maximale Anzahl der Iterationen.",
            zh="最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Iterações máximas",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-4,
            "lower_bound": 1e-6,
            "upper_bound": 1e-1,
        },
        description=MultilingualString(
            en="The tolerance for the optimisation.",
            es="La tolerancia para la optimización.",
            pt="A tolerância para a otimização.",
            de="Die Toleranz für die Optimierung.",
            zh="优化的收敛容差。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
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
                "A semente do gerador de números pseudoaleatórios. Passe um int "
                "para saída reproduzível, ou None para não definir uma semente."
            ),
            de=(
                "Der Seed des Pseudozufallszahlengenerators. Übergeben Sie eine ganze "
                "Zahl für "
                "reproduzierbare Ausgaben oder None, um keinen bestimmten Seed "
                "festzulegen."
            ),
            zh=(
                "伪随机数生成器的种子。传入整数以获得可复现的输出，"
                "传入 None 则不设定特定种子。"
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


class ElasticNetRegression(RegressionModel, SklearnLikeRegressor, _ElasticNet):
    """Elastic Net regression combining L1 and L2 penalties.

    Elastic Net minimises ``||y - Xw||^2 / (2*n) + alpha * l1_ratio * ||w||_1
    + alpha * (1 - l1_ratio) * 0.5 * ||w||^2``. The blend of L1 and L2 penalties
    overcomes Lasso's limitation with correlated features while still producing
    sparse solutions. Useful when there are many correlated features.

    Key hyperparameters include ``alpha``, ``l1_ratio``, ``fit_intercept``, and
    ``max_iter``. The implementation wraps scikit-learn's ``ElasticNet``.

    References
    ----------
    - [1] Zou, H. & Hastie, T. (2005). "Regularization and Variable Selection
           via the Elastic Net." JRSS-B, 67(2), 301-320.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html
    """

    SCHEMA = ElasticNetRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Elastic Net Regression",
        es="Regresión Elastic Net",
        pt="Regressão Elastic Net",
        de="ElasticNet-Regression",
        zh="弹性网络回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Linear regression combining L1 and L2 regularisation.",
        es="Regresión lineal que combina regularización L1 y L2.",
        pt="Regressão linear que combina regularização L1 e L2.",
        de="Lineare Regression mit kombinierter L1- und L2-Regularisierung.",
        zh="结合 L1 和 L2 正则化的线性回归。",
    )
    COLOR: str = "#26A69A"
    ICON: str = "Hub"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
