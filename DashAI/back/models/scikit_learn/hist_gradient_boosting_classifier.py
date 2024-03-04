from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.core.schema_fields import BaseSchema, float_field, int_field
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifierSchema(BaseSchema):
    """A gradient boosting classifier is a machine learning algorithm that combines
    multiple weak prediction models (typically decision trees) to create a strong
    predictive model by training the models sequentially, in which each new model is
    focused on correcting the errors made by the previous ones.
    """

    learning_rate: float_field(
        description="The learning rate, also known as shrinkage. This is used as a "
        "multiplicative factor for the leaves values. Use 1 for no shrinkage.",
        default=0.1,
        ge=0.0,
    )
    max_iter: int_field(
        description="The maximum number of iterations of the boosting process, i.e. "
        "the maximum number of trees for binary classification.",
        default=100,
        ge=0,
    )
    max_depth: int_field(
        description="The maximum depth of each tree. The depth of a tree is the "
        "number of edges to go from the root to the deepest leaf. Depth isn’t "
        "constrained by default.",
        default=1,
        ge=0,
    )
    max_leaf_nodes: int_field(
        description="The maximum number of leaves for each tree. Must be strictly "
        "greater than 1. If None, there is no maximum limit.",
        default=31,
        ge=2,
    )
    min_samples_leaf: int_field(
        description="The minimum number of samples required to be at a leaf node.",
        default=20,
        ge=1,
    )
    l2_regularization: float_field(
        description="The L2 regularization parameter. Use 0 for no regularization.",
        default=0.0,
        ge=0.0,
    )


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeModel, _HistGradientBoostingClassifier
):
    """Scikit-learn's HistGradientBoostingRegressor wrapper for DashAI."""

    SCHEMA = HistGradientBoostingClassifierSchema
