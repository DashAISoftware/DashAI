from sklearn.ensemble import RandomForestRegressor as _RandomForestRegressor

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
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RandomForestRegressionSchema(BaseSchema):
    """Random Forest Regressor for DashAI."""

    n_estimators: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 10,
            "upper_bound": 1000,
        },
        description="The number of trees in the forest.",
    )  # type: ignore

    criterion: schema_field(
        enum_field(enum=["squared_error", "absolute_error", "poisson"]),
        placeholder="squared_error",
        description="The function to measure the quality of a split.",
    )  # type: ignore

    max_depth: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="The maximum depth of the tree.",
    )  # type: ignore

    min_samples_split: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 20,
        },
        description="The minimum number of samples required to split "
        "an internal node.",
    )  # type: ignore

    min_samples_leaf: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 20,
        },
        description="The minimum number of samples required to be at a leaf node.",
    )  # type: ignore

    min_weight_fraction_leaf: schema_field(
        optimizer_float_field(ge=0.0, le=0.5),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.5,
        },
        description="The minimum weighted fraction of the sum total of weights"
        " required to be at a leaf node.",
    )  # type: ignore

    max_features: schema_field(
        union_type(
            optimizer_float_field(gt=0.0, le=1.0),
            enum_field(enum=["auto", "sqrt", "log2", None]),
        ),
        placeholder="auto",
        description="The number of features to consider when looking for the"
        " best split.",
    )  # type: ignore

    max_leaf_nodes: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="Grow trees with max_leaf_nodes in best-first fashion.",
    )  # type: ignore

    min_impurity_decrease: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.5,
        },
        description="A node will be split if this split induces a decrease of"
        " the impurity greater than or equal to this value.",
    )  # type: ignore

    bootstrap: schema_field(
        bool_field,
        placeholder=True,
        description="Whether bootstrap samples are used when building trees.",
    )  # type: ignore

    oob_score: schema_field(
        bool_field,
        placeholder=False,
        description="Whether to use out-of-bag samples to estimate the "
        "generalization score.",
    )  # type: ignore

    n_jobs: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="The number of jobs to run in parallel for both fit and predict.",
    )  # type: ignore

    random_state: schema_field(
        union_type(optimizer_int_field(ge=0), none_type(int)),
        placeholder=None,
        description="The seed of the pseudo-random number generator to use"
        " when shuffling the data.",
    )  # type: ignore

    verbose: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 0,
            "upper_bound": 100,
        },
        description="Controls the verbosity when fitting and predicting.",
    )  # type: ignore

    warm_start: schema_field(
        bool_field,
        placeholder=False,
        description="When set to True, reuse the solution of the previous "
        "call to fit and add more estimators to the ensemble.",
    )  # type: ignore

    ccp_alpha: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 1.0,
        },
        description="Complexity parameter used for Minimal Cost-Complexity Pruning.",
    )  # type: ignore

    max_samples: schema_field(
        union_type(optimizer_float_field(gt=0.0, le=1.0), none_type(float)),
        placeholder=None,
        description="If bootstrap is True, the number of samples to draw from"
        " X to train each base estimator.",
    )  # type: ignore

    monotonic_cst: schema_field(
        none_type((float)),
        placeholder=None,
        description="A constraint vector indicating the monotonicity "
        "constraint on each feature.",
    )  # type: ignore


class RandomForestRegression(
    RegressionModel, SklearnLikeRegressor, _RandomForestRegressor
):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""

    SCHEMA = RandomForestRegressionSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
