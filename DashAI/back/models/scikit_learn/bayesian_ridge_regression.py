from sklearn.linear_model import BayesianRidge as _BayesianRidge

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class BayesianRidgeRegressionSchema(BaseSchema):
    """Schema that configures the Bayesian Ridge Regression model.

    Bayesian Ridge estimates the parameters of a regression model using Bayesian
    inference. It includes regularisation parameters that are estimated from the
    data rather than set by the user. The underlying implementation is
    ``sklearn.linear_model.BayesianRidge``.
    """

    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 300,
            "lower_bound": 50,
            "upper_bound": 1000,
        },
        description=MultilingualString(
            en="Maximum number of iterations over the complete dataset.",
            es="Número máximo de iteraciones sobre el conjunto de datos completo.",
            pt="Número máximo de iterações sobre o conjunto de dados completo.",
            de="Maximale Anzahl von Iterationen über den vollständigen Datensatz.",
            zh="对完整数据集的最大迭代次数。",
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
            "fixed_value": 1e-3,
            "lower_bound": 1e-6,
            "upper_bound": 1e-1,
        },
        description=MultilingualString(
            en="Stop the algorithm if the weight update is smaller than tol.",
            es=("Detener el algoritmo si la actualización de pesos es menor que tol."),
            pt=("Parar o algoritmo se a atualização dos pesos for menor que tol."),
            de=(
                "Den Algorithmus stoppen, wenn die Gewichtsaktualisierung kleiner als "
                "tol ist."
            ),
            zh="若权重更新小于 tol，则停止算法。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore

    alpha_1: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-6,
            "lower_bound": 1e-10,
            "upper_bound": 1e-2,
        },
        description=MultilingualString(
            en="Shape parameter for the Gamma distribution prior over alpha.",
            es=("Parámetro de forma para la distribución Gamma previa sobre alfa."),
            pt=("Parâmetro de forma para a distribuição Gamma a priori sobre alfa."),
            de=("Formparameter für die Gamma-Verteilungs-Prior über Alpha."),
            zh="Alpha 先验 Gamma 分布的形状参数。",
        ),
        alias=MultilingualString(
            en="Alpha 1", es="Alfa 1", pt="Alfa 1", de="Alpha 1", zh="Alpha 1"
        ),
    )  # type: ignore

    alpha_2: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-6,
            "lower_bound": 1e-10,
            "upper_bound": 1e-2,
        },
        description=MultilingualString(
            en="Rate parameter for the Gamma distribution prior over alpha.",
            es=("Parámetro de tasa para la distribución Gamma previa sobre alfa."),
            pt=("Parâmetro de taxa para a distribuição Gamma a priori sobre alfa."),
            de=("Ratenparameter für die Gamma-Verteilungs-Prior über Alpha."),
            zh="Alpha 先验 Gamma 分布的速率参数。",
        ),
        alias=MultilingualString(
            en="Alpha 2", es="Alfa 2", pt="Alfa 2", de="Alpha 2", zh="Alpha 2"
        ),
    )  # type: ignore

    lambda_1: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-6,
            "lower_bound": 1e-10,
            "upper_bound": 1e-2,
        },
        description=MultilingualString(
            en="Shape parameter for the Gamma distribution prior over lambda.",
            es=("Parámetro de forma para la distribución Gamma previa sobre lambda."),
            pt=("Parâmetro de forma para a distribuição Gamma a priori sobre lambda."),
            de=("Formparameter für die Gamma-Verteilungs-Prior über Lambda."),
            zh="Lambda 先验 Gamma 分布的形状参数。",
        ),
        alias=MultilingualString(
            en="Lambda 1", es="Lambda 1", pt="Lambda 1", de="Lambda 1", zh="Lambda 1"
        ),
    )  # type: ignore

    lambda_2: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-6,
            "lower_bound": 1e-10,
            "upper_bound": 1e-2,
        },
        description=MultilingualString(
            en="Rate parameter for the Gamma distribution prior over lambda.",
            es=("Parámetro de tasa para la distribución Gamma previa sobre lambda."),
            pt=("Parâmetro de taxa para a distribuição Gamma a priori sobre lambda."),
            de=("Ratenparameter für die Gamma-Verteilungs-Prior über Lambda."),
            zh="Lambda 先验 Gamma 分布的速率参数。",
        ),
        alias=MultilingualString(
            en="Lambda 2", es="Lambda 2", pt="Lambda 2", de="Lambda 2", zh="Lambda 2"
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
            zh="是否为该模型计算截距。若为 False，则期望数据已被中心化。",
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
        ),
    )  # type: ignore


class BayesianRidgeRegression(RegressionModel, SklearnLikeRegressor, _BayesianRidge):
    """Bayesian Ridge regression with automatic regularisation estimation.

    BayesianRidge places Gamma priors over the regularisation parameters and
    estimates them from the data using the Expectation-Maximisation algorithm.
    This avoids the need for cross-validation to select ``alpha`` and provides
    predictive uncertainty estimates. It tends to be robust to over-fitting.

    Key hyperparameters include ``max_iter``, ``tol``, and the Gamma prior
    parameters ``alpha_1``, ``alpha_2``, ``lambda_1``, ``lambda_2``. The
    implementation wraps scikit-learn's ``BayesianRidge``.

    References
    ----------
    - [1] MacKay, D.J.C. (1992). "Bayesian Interpolation." Neural Computation, 4(3).
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.BayesianRidge.html
    """

    SCHEMA = BayesianRidgeRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Bayesian Ridge Regression",
        es="Regresión Ridge Bayesiana",
        pt="Regressão Ridge Bayesiana",
        de="Bayesische Ridge-Regression",
        zh="贝叶斯岭回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Bayesian regression with automatic regularisation estimation.",
        es="Regresión bayesiana con estimación automática de regularización.",
        pt="Regressão bayesiana com estimação automática de regularização.",
        de="Bayesische Regression mit automatischer Regularisierungsschätzung.",
        zh="具有自动正则化估计的贝叶斯回归。",
    )
    COLOR: str = "#7E57C2"
    ICON: str = "Psychology"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
