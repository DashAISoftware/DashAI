from sklearn.linear_model import Ridge as _Ridge

from DashAI.back.core.schema_fields import (
    BaseSchema,
    optimizer_int_field,
    optimizer_float_field,
    schema_field,
)

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RidgeRegressionSchema(BaseSchema):
    """Ridge regression is a linear model that includes L2 regularization."""

    alpha: schema_field(
        optimizer_float_field(gt=0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.1,
            "upper_bound": 10.0,
        },
        description="The 'alpha' parameter specifies the regularization strength. It must be a positive number.",
    )  # type: ignore
    fit_intercept: schema_field(
        bool,
        placeholder={
            "optimize": False,
            "fixed_value": True,
        },
        description="The 'fit_intercept' parameter determines whether to calculate the intercept for this model. It must be of type boolean.",
    )  # type: ignore
    copy_X: schema_field(
        bool,
        placeholder={
            "optimize": False,
            "fixed_value": True,
        },
        description="The 'copy_X' parameter determines whether to copy the input variables. It must be of type boolean.",
    )  # type: ignore
    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": None,
            "lower_bound": 1,
            "upper_bound": 1000,
        },
        description="The 'max_iter' parameter determines the maximum number of iterations for the solver. It must be a positive integer or -1 to indicate no limit.",
    )  # type: ignore
    tol: schema_field(
        optimizer_float_field(gt=0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 0.0001,
            "upper_bound": 0.01,
        },
        description="The 'tol' parameter determines the tolerance for the optimization. It must be a positive number.",
    )  # type: ignore
    solver: schema_field(
        str,
        placeholder={
            "optimize": False,
            "fixed_value": "auto",
        },
        description="The 'solver' parameter determines the solver to use in the computational routines. It must be one of 'auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga', or 'lbfgs'.",
        enum=["auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga", "lbfgs"],
    )  # type: ignore
    positive: schema_field(
        bool,
        placeholder={
            "optimize": False,
            "fixed_value": False,
        },
        description="The 'positive' parameter, when set to True, forces the coefficients to be positive. It must be of type boolean.",
    )  # type: ignore
    random_state: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": None,
            "lower_bound": 0,
            "upper_bound": 100,
        },
        description="The 'random_state' parameter determines the seed used by the random number generator. It must be an integer greater than or equal to 0, or null.",
    )  # type: ignore


class RidgeRegression(RegressionModel, SklearnLikeRegressor, _Ridge):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""

    SCHEMA = RidgeRegressionSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
