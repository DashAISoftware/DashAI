from sklearn.ensemble import GradientBoostingRegressor as _GBRegressor

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


class GradientBoostingRSchema(BaseSchema):
    """Gradient Boosting for regression."""

    loss: schema_field(
        enum_field(enum=["squared_error", "absolute_error", "huber", "quantile"]),
        placeholder="squared_error",
        description="Loss function to be optimized.",
    )  # type: ignore

    learning_rate: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.1,
            "lower_bound": 0.01,
            "upper_bound": 1.0,
        },
        description="Learning rate shrinks the contribution of each tree.",
    )  # type: ignore

    n_estimators: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 10,
            "upper_bound": 1000,
        },
        description="The number of boosting stages to be run.",
    )  # type: ignore

    subsample: schema_field(
        optimizer_float_field(gt=0.0, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.1,
            "upper_bound": 1.0,
        },
        description="The fraction of samples to be used for fitting the "
        "individual base learners.",
    )  # type: ignore

    criterion: schema_field(
        enum_field(enum=["friedman_mse", "mse", "mae"]),
        placeholder="friedman_mse",
        description="The function to measure the quality of a split.",
    )  # type: ignore

    min_samples_split: schema_field(
        optimizer_float_field(gt=0.0, le=1.0),
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
        optimizer_float_field(gt=0.0, le=0.5),
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
        " (of all the input samples) required to be at a leaf node.",
    )  # type: ignore

    max_depth: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=3,
        description="The maximum depth of the individual regression estimators.",
    )  # type: ignore

    min_impurity_decrease: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.5,
        },
        description="A node will be split if this split induces a decrease of "
        "the impurity greater than or equal to this value.",
    )  # type: ignore

    random_state: schema_field(
        union_type(optimizer_int_field(ge=0), none_type(int)),
        placeholder=None,
        description="The seed of the pseudo-random number generator to use"
        " when shuffling the data.",
    )  # type: ignore

    max_features: schema_field(
        union_type(
            optimizer_float_field(gt=0.0, le=1.0),
            enum_field(enum=["sqrt", "log2", None]),
        ),
        placeholder=None,
        description="The number of features to consider when looking for "
        "the best split.",
    )  # type: ignore

    alpha: schema_field(
        optimizer_float_field(gt=0.0, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.9,
            "lower_bound": 0.1,
            "upper_bound": 1.0,
        },
        description="The alpha-quantile of the Huber loss function and the"
        " quantile loss function.",
    )  # type: ignore

    verbose: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 0,
            "upper_bound": 100,
        },
        description="Enable verbose output.",
    )  # type: ignore

    max_leaf_nodes: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="Grow trees with max_leaf_nodes in best-first fashion.",
    )  # type: ignore

    warm_start: schema_field(
        bool_field,
        placeholder=False,
        description="When set to True, reuse the solution of the previous call"
        "to fit and add more estimators to the ensemble.",
    )  # type: ignore

    validation_fraction: schema_field(
        optimizer_float_field(gt=0.0, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.1,
            "lower_bound": 0.1,
            "upper_bound": 0.5,
        },
        description="The proportion of training data to set aside as "
        "validation set for early stopping.",
    )  # type: ignore

    n_iter_no_change: schema_field(
        union_type(optimizer_int_field(ge=1), none_type(int)),
        placeholder=None,
        description="The number of iterations with no improvement to wait "
        "before stopping the training.",
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0001,
            "lower_bound": 1e-5,
            "upper_bound": 1e-1,
        },
        description="Tolerance for the early stopping.",
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


class GradientBoostingR(RegressionModel, SklearnLikeRegressor, _GBRegressor):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""

    SCHEMA = GradientBoostingRSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
