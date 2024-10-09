from sklearn.linear_model import LogisticRegression as _LogisticRegression

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class LogisticRegressionSchema(BaseSchema):
    """Logistic Regression is a supervised classification method that uses a linear
    model plus a a logistic funcion to predict binary outcomes (it can be configured
    as multiclass via the one-vs-rest strategy).
    """

    penalty: schema_field(
        enum_field(enum=["l2", "l1", "elasticnet"]),
        placeholder="l2",
        description="Specify the norm of the penalty",
    )  # type: ignore
    tol: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 0.001,
            "upper_bound": 5,
        },
        description="Tolerance for stopping criteria.",
    )  # type: ignore
    C: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 7.0,
        },
        description="Inverse of regularization strength, smaller values specify "
        "stronger regularization. Must be a positive number.",
    )  # type: ignore
    max_iter: schema_field(
        optimizer_int_field(ge=50),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 50,
            "upper_bound": 250,
        },
        description="Maximum number of iterations taken for the solvers to converge.",
    )  # type: ignore


class LogisticRegression(
    TabularClassificationModel, SklearnLikeClassifier, _LogisticRegression
):
    """Scikit-learn's Logistic Regression wrapper for DashAI."""

    SCHEMA = LogisticRegressionSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
