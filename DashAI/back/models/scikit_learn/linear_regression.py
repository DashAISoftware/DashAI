from sklearn.linear_model import LinearRegression as _LinearRegression

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class LinearRegressionSchema(BaseSchema):
    """Schema that configures the Ordinary Least-Squares Linear Regression model.

    Linear Regression fits a linear model by minimising the residual sum of squares
    between observed targets and predicted values. It is used for tabular regression
    tasks. The underlying implementation is
    ``sklearn.linear_model.LinearRegression``.
    """

    fit_intercept: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Whether to calculate the intercept for this model. "
                "If set to False, no intercept will be used in calculations "
                "(e.g., data is expected to be centered)."
            ),
            es=(
                "Si se debe calcular el intercepto para este modelo. "
                "Si se establece en False, no se usará intercepto en los cálculos "
                "(ej., se espera que los datos estén centrados)."
            ),
            pt=(
                "Se deve calcular o intercepto para este modelo. "
                "Se definido como False, nenhum intercepto será usado nos cálculos "
                "(ex., espera-se que os dados estejam centrados)."
            ),
            de=(
                "Ob der Achsenabschnitt für dieses Modell berechnet werden soll. "
                "Bei False wird kein Achsenabschnitt in den Berechnungen verwendet "
                "(z.B. wird erwartet, dass die Daten zentriert sind)."
            ),
            zh=(
                "是否为该模型计算截距。"
                "若设为 False，则计算中不使用截距"
                "（即假设数据已中心化）。"
            ),
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
        ),
    )  # type: ignore

    copy_X: schema_field(  # noqa: N815
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="If True, X will be copied; else, it may be overwritten.",
            es="Si es True, X será copiado; si no, puede ser sobrescrito.",
            pt="Se True, X será copiado; caso contrário, pode ser sobrescrito.",
            de="Wenn True, wird X kopiert; andernfalls kann es überschrieben werden.",
            zh="若为 True，则复制 X；否则可能被覆盖。",
        ),
        alias=MultilingualString(
            en="Copy X", es="Copiar X", pt="Copiar X", de="X kopieren", zh="复制 X"
        ),
    )  # type: ignore

    n_jobs: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The number of jobs to use for the computation. "
                "None means 1 job, while -1 means using all processors."
            ),
            es=(
                "El número de trabajos a usar para el cálculo. "
                "None significa 1 trabajo, mientras que -1 significa usar todos "
                "los procesadores."
            ),
            pt=(
                "O número de jobs a usar para o cálculo. "
                "None significa 1 job, enquanto -1 significa usar todos "
                "os processadores."
            ),
            de=(
                "Die Anzahl der Jobs für die Berechnung. "
                "None bedeutet 1 Job, -1 bedeutet alle Prozessoren verwenden."
            ),
            zh=("用于计算的并行作业数。None 表示 1 个作业，-1 表示使用所有处理器。"),
        ),
        alias=MultilingualString(
            en="N jobs", es="N trabajos", pt="N jobs", de="Anzahl Jobs", zh="并行作业数"
        ),
    )  # type: ignore

    positive: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en="When set to True, forces the coefficients to be positive.",
            es="Cuando se establece en True, fuerza los coeficientes a ser positivos.",
            pt="Quando definido como True, força os coeficientes a serem positivos.",
            de="Wenn True, werden die Koeffizienten auf positive Werte gezwungen.",
            zh="若设为 True，则强制系数为非负值。",
        ),
        alias=MultilingualString(
            en="Positive", es="Positivo", pt="Positivo", de="Positiv", zh="正系数"
        ),
    )  # type: ignore


class LinearRegression(RegressionModel, SklearnLikeRegressor, _LinearRegression):
    """Ordinary least-squares linear regression model.

    Linear Regression models the relationship between one or more input features and
    a continuous target by fitting a linear equation ``y = Xw + b``. The coefficients
    ``w`` and intercept ``b`` are estimated by minimising the residual sum of squares
    ``||y - Xw||^2``, which has a closed-form solution via the normal equations or
    can be computed via singular value decomposition.

    This model has no regularisation, so it can overfit when the number of features
    is large or predictors are highly collinear (consider ``RidgeRegression`` in those
    cases). Key hyperparameters are ``fit_intercept``, ``positive`` (constraint to
    nonnegative coefficients), ``copy_X``, and ``n_jobs``. The implementation wraps
    scikit-learn's ``LinearRegression``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
    """

    SCHEMA = LinearRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Linear Regression",
        es="Regresión Lineal",
        pt="Regressão Linear",
        de="Lineare Regression",
        zh="线性回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Ordinary least squares linear regression.",
        es="Regresión lineal de mínimos cuadrados ordinarios.",
        pt="Regressão linear de mínimos quadrados ordinários.",
        de="Lineare Regression der gewöhnlichen kleinsten Quadrate.",
        zh="普通最小二乘线性回归。",
    )
    COLOR: str = "#3F51B5"
    ICON: str = "ShowChart"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
