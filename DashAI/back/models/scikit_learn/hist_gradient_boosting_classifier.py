from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifierSchema(BaseSchema):
    """A gradient boosting classifier is a machine learning algorithm that combines
    multiple weak prediction models (typically decision trees) to create a strong
    predictive model by training the models sequentially, in which each new model is
    focused on correcting the errors made by the previous ones.
    """

    learning_rate: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.1,
            "lower_bound": 0.1,
            "upper_bound": 1,
        },
        description="The learning rate, also known as shrinkage. This is used as a "
        "multiplicative factor for the leaves values. Use 1 for no shrinkage.",
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 100,
            "upper_bound": 250,
        },
        description="The maximum number of iterations of the boosting process, i.e. "
        "the maximum number of trees for binary classification.",
    )  # type: ignore
    max_depth: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 10,
        },
        description="The maximum depth of each tree. The depth of a tree is the "
        "number of edges to go from the root to the deepest leaf. Depth isn’t "
        "constrained by default.",
    )  # type: ignore
    max_leaf_nodes: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 31,
            "lower_bound": 10,
            "upper_bound": 40,
        },
        description="The maximum number of leaves for each tree. Must be strictly "
        "greater than 1. If None, there is no maximum limit.",
    )  # type: ignore
    min_samples_leaf: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 20,
            "lower_bound": 2,
            "upper_bound": 25,
        },
        description="The minimum number of samples required to be at a leaf node.",
    )  # type: ignore
    l2_regularization: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 1.0,
        },
        description="The L2 regularization parameter. Use 0 for no regularization.",
    )  # type: ignore


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _HistGradientBoostingClassifier
):
    """Scikit-learn's HistGradientBoostingRegressor wrapper for DashAI."""

    SCHEMA = HistGradientBoostingClassifierSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
