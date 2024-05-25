from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifierSchema(BaseSchema):
    """Random Forest (RF) is an ensemble machine learning algorithm that achieves
    enhanced performance by combining multiple decision trees and aggregating their
    outputs.
    """

    n_estimators: schema_field(
        int_field(ge=1),
        placeholder=100,
        description="The 'n_estimators' parameter corresponds to the number of "
        "decision trees. It must be an integer greater than or equal to 1.",
    )  # type: ignore
    max_depth: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description="The 'max_depth' parameter corresponds to the maximum depth of "
        "the tree. It must be an integer greater than or equal to 1.",
    )  # type: ignore
    min_samples_split: schema_field(
        int_field(ge=2),
        placeholder=2,
        description="The 'min_samples_split' parameter is the minimum number of "
        "samples required to split an internal node. It must be a number greater than "
        "or equal to 2.",
    )  # type: ignore
    min_samples_leaf: schema_field(
        int_field(ge=1),
        placeholder=1,
        description="The 'min_samples_leaf' parameter is the minimum number of "
        "samples required to be at a leaf node. It must be a number greater than or "
        "equal to 1.",
    )  # type: ignore
    max_leaf_nodes: schema_field(
        none_type(int_field(ge=2)),
        placeholder=None,
        description="The 'max_leaf_nodes' parameter must be an integer greater "
        "than or equal to 2.",
    )  # type: ignore
    random_state: schema_field(
        none_type(int_field(ge=0)),
        placeholder=None,
        description="The 'random_state' parameter must be an integer greater than "
        "or equal to 0.",
    )  # type: ignore


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier
):
    """Scikit-learn's Random Forest classifier wrapper for DashAI."""

    SCHEMA = RandomForestClassifierSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        super().__init__(**kwargs)
