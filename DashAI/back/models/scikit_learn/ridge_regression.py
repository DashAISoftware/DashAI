from sklearn.linear_model import Ridge as _Ridge

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RidgeRegressionSchema(BaseSchema):
    """Schema that configures the Ridge Regression model.

    Ridge Regression is a linear regression method that adds an L2 (squared-norm)
    penalty on the coefficients to the ordinary least-squares objective, shrinking
    coefficients towards zero to reduce overfitting and handle collinearity. It is
    used for tabular regression tasks. The underlying implementation is
    ``sklearn.linear_model.Ridge``.
    """

    alpha: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 10,
        },
        description=MultilingualString(
            en=(
                "Regularization strength; must be a positive float. "
                "Larger values specify stronger regularization."
            ),
            es=(
                "Fuerza de regularización; debe ser un float positivo. "
                "Valores más grandes especifican una regularización más fuerte."
            ),
            pt=(
                "Força de regularização; deve ser um float positivo. "
                "Valores maiores especificam uma regularização mais forte."
            ),
            de=(
                "Regularisierungsstärke; muss ein positiver Float sein. "
                "Größere Werte bedeuten stärkere Regularisierung."
            ),
            zh="正则化强度；必须为正浮点数。值越大，正则化越强。",
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
                "Se o intercepto deve ser calculado para este modelo. "
                "Se definido como False, nenhum intercepto será usado nos cálculos "
                "(ex., espera-se que os dados estejam centrados)."
            ),
            de=(
                "Ob der Achsenabschnitt für dieses Modell berechnet werden soll. "
                "Bei False wird kein Achsenabschnitt in den Berechnungen verwendet "
                "(z.B. wird erwartet, dass die Daten zentriert sind)."
            ),
            zh=(
                "是否为模型计算截距。"
                "设为 False 时，计算中不使用截距（如数据已中心化）。"
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

    max_iter: schema_field(
        optimizer_int_field(ge=10),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 10,
            "upper_bound": 10000,
        },
        description=MultilingualString(
            en="Maximum number of iterations for conjugate gradient solver.",
            es=(
                "Número máximo de iteraciones para el "
                "solucionador de gradiente conjugado."
            ),
            pt=(
                "Número máximo de iterações para o solucionador de gradiente conjugado."
            ),
            de="Maximale Anzahl von Iterationen für den konjugierten Gradientenlöser.",
            zh="共轭梯度求解器的最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 1e-5,
            "upper_bound": 1e-1,
        },
        description=MultilingualString(
            en="Precision of the solution.",
            es="Precisión de la solución.",
            pt="Precisão da solução.",
            de="Genauigkeit der Lösung.",
            zh="求解精度。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore
    solver: search_space(
        enum_field(
            enum=["auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga"]
        ),
        fixed="auto",
        description=MultilingualString(
            en=(
                "Solver to use in the computation. 'auto' chooses the "
                "solver automatically based on the type of data."
            ),
            es=(
                "Solucionador a usar en el cálculo. 'auto' elige el "
                "solucionador automáticamente basado en el tipo de datos."
            ),
            pt=(
                "Solucionador a usar no cálculo. 'auto' escolhe o "
                "solucionador automaticamente com base no tipo de dados."
            ),
            de=(
                "Löser für die Berechnung. 'auto' wählt den Löser "
                "automatisch basierend auf dem Datentyp."
            ),
            zh="计算所用的求解器。'auto' 根据数据类型自动选择求解器。",
        ),
        alias=MultilingualString(
            en="Solver", es="Solucionador", pt="Solucionador", de="Löser", zh="求解器"
        ),
    )  # type: ignore
    positive: search_space(
        bool_field(),
        fixed=False,
        description=MultilingualString(
            en="When set to True, forces the coefficients to be positive.",
            es="Cuando se establece en True, fuerza los coeficientes a ser positivos.",
            pt="Quando definido como True, força os coeficientes a serem positivos.",
            de="Wenn True, werden die Koeffizienten auf positive Werte gezwungen.",
            zh="设为 True 时，强制系数为正值。",
        ),
        alias=MultilingualString(
            en="Positive", es="Positivo", pt="Positivo", de="Positiv", zh="正值"
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(optimizer_int_field(ge=0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The seed of the pseudo random number generator to use "
                "when shuffling the data. Pass an int for reproducible output across "
                "multiple function calls, or None to not set a specific seed."
            ),
            es=(
                "La semilla del generador de números pseudoaleatorios a usar "
                "al mezclar los datos. Pase un int para salida reproducible entre "
                "múltiples llamadas, o None para no establecer una semilla específica."
            ),
            pt=(
                "A semente do gerador de números pseudoaleatórios a usar "
                "ao embaralhar os dados. Passe um int para saída reproduzível entre "
                "múltiplas chamadas, ou None para não definir uma semente específica."
            ),
            de=(
                "Der Seed des Pseudozufallszahlengenerators beim Mischen der Daten. "
                "Übergeben Sie eine ganze Zahl für reproduzierbare Ausgaben oder "
                "None, um keinen bestimmten Seed festzulegen."
            ),
            zh=(
                "数据混洗时使用的伪随机数生成器种子。"
                "传入整数可在多次调用间获得可重复输出，传入 None 则不设定特定种子。"
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


class RidgeRegression(RegressionModel, SklearnLikeRegressor, _Ridge):
    """Ridge regression with L2 regularisation to reduce coefficient magnitude.

    Ridge Regression minimises the penalised least-squares objective
    ``||y - Xw||^2 + alpha * ||w||^2``, where ``alpha`` is the regularisation
    strength. The L2 penalty shrinks all coefficients towards zero but does not
    set any of them exactly to zero, making Ridge suitable for situations where
    many predictors contribute small effects or when features are highly collinear.

    The solver (``svd``, ``cholesky``, ``lsqr``, ``sparse_cg``, ``sag``,
    ``saga``, or ``auto``) is selected based on data characteristics. Key
    hyperparameters are ``alpha``, ``fit_intercept``, ``solver``, and ``tol``.
    The implementation wraps scikit-learn's ``Ridge``.

    References
    ----------
    - [1] Hoerl, A.E. & Kennard, R.W. (1970). "Ridge Regression: Biased
           Estimation for Nonorthogonal Problems." Technometrics, 12(1), 55-67.
           https://doi.org/10.1080/00401706.1970.10488634
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html
    """

    SCHEMA = RidgeRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Ridge Regression",
        es="Regresión Ridge",
        pt="Regressão Ridge",
        de="Ridge-Regression",
        zh="岭回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Linear regression with L2 regularization.",
        es="Regresión lineal con regularización L2.",
        pt="Regressão linear com regularização L2.",
        de="Lineare Regression mit L2-Regularisierung.",
        zh="使用 L2 正则化的线性回归。",
    )
    COLOR: str = "#2196F3"
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
