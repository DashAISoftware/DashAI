from sklearn.linear_model import LinearRegression as _LinearRegression

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    none_type,
    optimizer_int_field,
    schema_field,
    union_type,
)
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import (
    SklearnLikeRegressor,
)


class LinearRegressionSchema(BaseSchema):
    """Linear regression model with optional intercept."""

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

    n_jobs: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="The number of jobs to use for the computation. "
        "None means 1 job, while -1 means using all processors.",
    )  # type: ignore

    positive: schema_field(
        bool_field,
        placeholder=False,
        description="When set to True, forces the coefficients to be positive.",
    )  # type: ignore


class LinearRegression(RegressionModel, SklearnLikeRegressor, _LinearRegression):
    """Scikit-learn's Linear Regression wrapper for DashAI."""

    SCHEMA = LinearRegressionSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
