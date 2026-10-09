from sklearn.linear_model import Lasso as _Lasso

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class LassoRegressionSchema(BaseSchema):
    """Schema that configures the Lasso Regression model.

    Lasso (Least Absolute Shrinkage and Selection Operator) adds an L1 penalty on
    the absolute values of coefficients, driving some of them exactly to zero,
    which performs implicit feature selection. The underlying implementation is
    ``sklearn.linear_model.Lasso``.
    """

    alpha: search_space(
        float_field(ge=0.0),
        fixed=1.0,
        low=0.0001,
        high=10.0,
        description=MultilingualString(
            en=(
                "Regularisation strength. Larger values specify stronger "
                "regularisation. alpha=0 is equivalent to OLS."
            ),
            es=(
                "Fuerza de regularización. Valores más grandes especifican "
                "regularización más fuerte. alpha=0 es equivalente a MCO."
            ),
            pt=(
                "Força de regularização. Valores maiores especificam "
                "regularização mais forte. alpha=0 é equivalente a MQO."
            ),
            de=(
                "Regularisierungsstärke. Größere Werte bedeuten stärkere "
                "Regularisierung. alpha=0 entspricht OLS."
            ),
            zh="正则化强度。值越大正则化越强。alpha=0 等价于 OLS。",
        ),
        alias=MultilingualString(
            en="Alpha", es="Alfa", pt="Alfa", de="Alpha", zh="Alpha"
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
            zh="是否为模型计算截距。若为 False，则数据应已居中。",
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
        ),
    )  # type: ignore

    max_iter: search_space(
        int_field(ge=100),
        fixed=1000,
        low=100,
        high=10000,
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
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore

    tol: search_space(
        float_field(ge=0.0),
        fixed=0.0001,
        low=1e-06,
        high=0.1,
        description=MultilingualString(
            en="The tolerance for the optimisation.",
            es="La tolerancia para la optimización.",
            pt="A tolerância para a otimização.",
            de="Die Toleranz für die Optimierung.",
            zh="优化的容差。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
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
            zh=(
                "伪随机数生成器的种子。传入整数以获得可复现的输出，"
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


class LassoRegression(RegressionModel, SklearnLikeRegressor, _Lasso):
    """Lasso regression with L1 regularisation for sparse coefficient solutions.

    Lasso minimises the OLS objective plus an L1 penalty
    ``||y - Xw||^2 / (2*n) + alpha * ||w||_1``. The L1 term sets many
    coefficients exactly to zero, performing automatic feature selection. Lasso is
    particularly useful when there are many features but only a few are expected to
    be relevant.

    Key hyperparameters include ``alpha``, ``fit_intercept``, ``max_iter``, and
    ``tol``. The implementation wraps scikit-learn's ``Lasso``.

    References
    ----------
    - [1] Tibshirani, R. (1996). "Regression Shrinkage and Selection via the Lasso."
           Journal of the Royal Statistical Society B, 58(1), 267-288.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html
    """

    SCHEMA = LassoRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Lasso Regression",
        es="Regresión Lasso",
        pt="Regressão Lasso",
        de="Lasso-Regression",
        zh="Lasso 回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Linear regression with L1 regularisation for feature selection.",
        es="Regresión lineal con regularización L1 para selección de características.",
        pt="Regressão linear com regularização L1 para seleção de características.",
        de="Lineare Regression mit L1-Regularisierung für Merkmalsselektion.",
        zh="使用 L1 正则化进行特征选择的线性回归。",
    )
    COLOR: str = "#29B6F6"
    ICON: str = "SelectAll"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
