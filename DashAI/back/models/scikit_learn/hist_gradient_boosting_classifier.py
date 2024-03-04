from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifierSchema(BaseSchema):
    """A gradient boosting classifier is a machine learning algorithm that combines
    multiple weak prediction models (typically decision trees) to create a strong
    predictive model by training the models sequentially, in which each new model is
    focused on correcting the errors made by the previous ones.
    """

    learning_rate: schema_field(
        float_field(ge=0.0),
        placeholder=0.1,
        description="The learning rate, also known as shrinkage. This is used as a "
        "multiplicative factor for the leaves values. Use 1 for no shrinkage.",
    )  # type: ignore

    max_iter: schema_field(
        int_field(ge=0),
        placeholder=100,
        description="The maximum number of iterations of the boosting process, i.e. "
        "the maximum number of trees for binary classification.",
    )  # type: ignore
    max_depth: schema_field(
        int_field(ge=0),
        placeholder=1,
        description="The maximum depth of each tree. The depth of a tree is the "
        "number of edges to go from the root to the deepest leaf. Depth isn’t "
        "constrained by default.",
    )  # type: ignore
    max_leaf_nodes: schema_field(
        int_field(ge=2),
        placeholder=31,
        description="The maximum number of leaves for each tree. Must be strictly "
        "greater than 1. If None, there is no maximum limit.",
    )  # type: ignore
    min_samples_leaf: schema_field(
        int_field(ge=1),
        placeholder=20,
        description="The minimum number of samples required to be at a leaf node.",
    )  # type: ignore
    l2_regularization: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description="The L2 regularization parameter. Use 0 for no regularization.",
    )  # type: ignore


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeModel, _HistGradientBoostingClassifier
):
    """Scikit-learn's HistGradientBoostingRegressor wrapper for DashAI."""

    SCHEMA = HistGradientBoostingClassifierSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        super().__init__(**kwargs)
