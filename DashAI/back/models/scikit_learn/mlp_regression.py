from sklearn.neural_network import MLPRegressor as _MLPregressor

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


class MLPRegressorSchema(BaseSchema):
    """MLP Regressor for DashAI."""

    activation: schema_field(
        enum_field(enum=["identity", "logistic", "tanh", "relu"]),
        placeholder="relu",
        description="Activation function for the hidden layer.",
    )  # type: ignore

    solver: schema_field(
        enum_field(enum=["lbfgs", "sgd", "adam"]),
        placeholder="adam",
        description="The solver for weight optimization.",
    )  # type: ignore

    alpha: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0001,
            "lower_bound": 1e-6,
            "upper_bound": 1e-1,
        },
        description="L2 penalty (regularization term) parameter.",
    )  # type: ignore

    batch_size: schema_field(
        union_type(optimizer_int_field(ge=1), enum_field(enum=["auto"])),
        placeholder="auto",
        description="Size of minibatches for stochastic optimizers.",
    )  # type: ignore

    learning_rate: schema_field(
        enum_field(enum=["constant", "invscaling", "adaptive"]),
        placeholder="constant",
        description="Learning rate schedule for weight updates.",
    )  # type: ignore

    learning_rate_init: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 1e-5,
            "upper_bound": 1e-1,
        },
        description="The initial learning rate used.",
    )  # type: ignore

    power_t: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.5,
            "lower_bound": 0.1,
            "upper_bound": 0.9,
        },
        description="The exponent for inverse scaling learning rate.",
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 200,
            "lower_bound": 50,
            "upper_bound": 1000,
        },
        description="Maximum number of iterations.",
    )  # type: ignore

    shuffle: schema_field(
        bool_field,
        placeholder=True,
        description="Whether to shuffle samples in each iteration.",
    )  # type: ignore

    random_state: schema_field(
        union_type(optimizer_int_field(ge=0), none_type(int)),
        placeholder=None,
        description="The seed of the pseudo-random number generator to use "
        "when shuffling the data.",
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0001,
            "lower_bound": 1e-6,
            "upper_bound": 1e-2,
        },
        description="Tolerance for the optimization.",
    )  # type: ignore

    verbose: schema_field(
        bool_field,
        placeholder=False,
        description="Whether to print progress messages to stdout.",
    )  # type: ignore

    warm_start: schema_field(
        bool_field,
        placeholder=False,
        description="When set to True, reuse the solution of the previous call"
        " to fit as initialization.",
    )  # type: ignore

    momentum: schema_field(
        optimizer_float_field(ge=0.0, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.9,
            "lower_bound": 0.0,
            "upper_bound": 1.0,
        },
        description="Momentum for gradient descent update.",
    )  # type: ignore

    nesterovs_momentum: schema_field(
        bool_field,
        placeholder=True,
        description="Whether to use Nesterov’s momentum.",
    )  # type: ignore

    early_stopping: schema_field(
        bool_field,
        placeholder=False,
        description="Whether to use early stopping to terminate training when"
        " validation score is not improving.",
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

    beta_1: schema_field(
        optimizer_float_field(gt=0.0, lt=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.9,
            "lower_bound": 0.1,
            "upper_bound": 0.999,
        },
        description="Exponential decay rate for estimates of first moment"
        " vector in Adam optimizer.",
    )  # type: ignore

    beta_2: schema_field(
        optimizer_float_field(gt=0.0, lt=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.999,
            "lower_bound": 0.1,
            "upper_bound": 0.999,
        },
        description="Exponential decay rate for estimates of second moment"
        " vector in Adam optimizer.",
    )  # type: ignore

    epsilon: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-08,
            "lower_bound": 1e-10,
            "upper_bound": 1e-6,
        },
        description="Value for numerical stability in Adam optimizer.",
    )  # type: ignore

    n_iter_no_change: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 10,
            "lower_bound": 1,
            "upper_bound": 50,
        },
        description="Maximum number of epochs to not meet tol improvement.",
    )  # type: ignore

    max_fun: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 15000,
            "lower_bound": 1000,
            "upper_bound": 20000,
        },
        description="Maximum number of loss function calls. Only used "
        " if solver='lbfgs'.",
    )  # type: ignore


class MLPRegression(RegressionModel, SklearnLikeRegressor, _MLPregressor):
    """Scikit-learn's MLP Regression wrapper for DashAI."""

    SCHEMA = MLPRegressorSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
