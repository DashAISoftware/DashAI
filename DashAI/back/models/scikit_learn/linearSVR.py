from sklearn.svm import LinearSVR as _LinearSVR

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
    union_type,
)
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import (
    SklearnLikeRegressor,
)


class LinearSVRSchema(BaseSchema):
    """Support Vector Regression (SVR) using a linear kernel."""

    epsilon: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 1,
        },
        description="Epsilon parameter that specifies the epsilon-tube within "
        "which no penalty is associated.",
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0001,
            "lower_bound": 1e-5,
            "upper_bound": 1e-1,
        },
        description="Tolerance for stopping criterion.",
    )  # type: ignore

    C: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.1,
            "upper_bound": 10,
        },
        description="Regularization parameter. The strength of the regularization "
        "is inversely proportional to C.",
    )  # type: ignore

    loss: schema_field(
        enum_field(enum=["epsilon_insensitive", "squared_epsilon_insensitive"]),
        placeholder="epsilon_insensitive",
        description="Specifies the loss function. 'epsilon_insensitive' is "
        "the standard SVR loss.",
    )  # type: ignore

    fit_intercept: schema_field(
        bool_field,
        placeholder=True,
        description="Whether to calculate the intercept for this model.",
    )  # type: ignore

    intercept_scaling: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.1,
            "upper_bound": 10,
        },
        description="When fit_intercept is True, instance vector x becomes "
        "[x, self.intercept_scaling] in the primal problem.",
    )  # type: ignore

    dual: schema_field(
        bool_field,
        placeholder=True,
        description="Select the algorithm to either solve the dual or primal"
        " optimization problem.",
    )  # type: ignore

    verbose: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 0,
            "upper_bound": 100,
        },
        description="Enable verbose output. Note that this setting takes "
        "advantage of a per-process runtime setting in libsvm.",
    )  # type: ignore

    random_state: schema_field(
        union_type(optimizer_int_field(ge=0), none_type(int)),
        placeholder=None,
        description="The seed of the pseudo-random number generator to use"
        " when shuffling the data.",
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1000,
            "lower_bound": 100,
            "upper_bound": 10000,
        },
        description="The maximum number of iterations to be run.",
    )  # type: ignore


class LinearSVR(RegressionModel, SklearnLikeRegressor, _LinearSVR):
    """Scikit-learn's Linear Support Vector Regression (LinearSVR)
    wrapper for DashAI."""

    SCHEMA = LinearSVRSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
