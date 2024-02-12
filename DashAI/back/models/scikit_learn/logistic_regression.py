from sklearn.linear_model import LogisticRegression as _LogisticRegression

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class LogisticRegressionSchema(BaseSchema):
    """Logistic Regression is a supervised classification method that uses a linear
    model plus a a logistic funcion to predict binary outcomes (it can be configured
    as multiclass via the one-vs-rest strategy).
    """

    penalty: schema_field(
        none_type(string_field(enum=["l2", "l1", "elasticnet"])),
        placeholder="l2",
        description="Specify the norm of the penalty",
    )  # type: ignore
    tol: schema_field(
        float_field(ge=0.0),
        placeholder=0.0001,
        description="Tolerance for stopping criteria.",
    )  # type: ignore
    C: schema_field(
        float_field(ge=0.0),
        placeholder=1.0,
        description="Inverse of regularization strength, smaller values specify "
        "stronger regularization. Must be a positive number.",
    )  # type: ignore
    max_iter: schema_field(
        int_field(ge=50),
        placeholder=100,
        description="Maximum number of iterations taken for the solvers to converge.",
    )  # type: ignore


class LogisticRegression(
    TabularClassificationModel, SklearnLikeModel, _LogisticRegression
):
    """Scikit-learn's Logistic Regression wrapper for DashAI."""

    SCHEMA = LogisticRegressionSchema
