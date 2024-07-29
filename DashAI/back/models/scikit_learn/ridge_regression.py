from sklearn.linear_model import Ridge as _Ridge

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


class RidgeRegressionSchema(BaseSchema):
    """Ridge regression is a linear model that includes L2 regularization."""

    alpha: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.1,
            "upper_bound": 10.0,
        },
        description="Regularization strength; must be a positive float. "
        "Larger values specify stronger regularization.",
    )  # type: ignore

    fit_intercept: schema_field(
        bool_field,
        placeholder=True,
        description="Whether to calculate the intercept for this model. "
        "If set to False, no intercept will be used in calculations "
        "(e.g., data is expected to be centered).",
    )  # type: ignore

    copy_x: schema_field(
        bool_field,
        placeholder=True,
        description="If True, X will be copied; else, it may be overwritten.",
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1000,
            "lower_bound": 100,
            "upper_bound": 10000,
        },
        description="Maximum number of iterations for conjugate gradient solver.",
    )  # type: ignore
    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 1e-5,
            "upper_bound": 1e-1,
        },
        description="Precision of the solution.",
    )  # type: ignore
    solver: schema_field(
        enum_field(
            enum=["auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga"]
        ),
        placeholder="auto",
        description="Solver to use in the computation. ‘auto’ chooses the "
        "solver automatically based on the type of data.",
    )  # type: ignore
    positive: schema_field(
        bool_field,
        placeholder=False,
        description="When set to True, forces the coefficients to be positive.",
    )  # type: ignore
    random_state: schema_field(
        union_type(optimizer_int_field(ge=0), none_type(int)),
        placeholder=None,
        description="The seed of the pseudo random number generator to use "
        "when shuffling the data. Pass an int for reproducible output across "
        "multiple function calls, or None to not set a specific seed.",
    )  # type: ignore


class RidgeRegression(RegressionModel, SklearnLikeRegressor, _Ridge):
    """Scikit-learn's Ridge regression wrapper for DashAI."""

    SCHEMA = RidgeRegressionSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
