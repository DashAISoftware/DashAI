from typing import Optional

from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.core.schema_fields import BaseSchema, int_field
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifierSchema(BaseSchema):
    """Random Forest (RF) is an ensemble machine learning algorithm that achieves
    enhanced performance by combining multiple decision trees and aggregating their
    outputs.
    """

    n_estimators: int_field(
        description="The 'n_estimators' parameter corresponds to the number of "
        "decision trees. It must be an integer greater than or equal to 1.",
        default=100,
        ge=1,
    )
    max_depth: Optional[
        int_field(
            description="The 'max_depth' parameter corresponds to the maximum depth of "
            "the tree. It must be an integer greater than or equal to 1.",
            default=None,
            ge=1,
        )
    ]
    min_samples_split: int_field(
        description="The 'min_samples_split' parameter is the minimum number of "
        "samples required to split an internal node. It must be a number greater than "
        "or equal to 2.",
        default=2,
        ge=2,
    )
    min_samples_leaf: int_field(
        description="The 'min_samples_leaf' parameter is the minimum number of "
        "samples required to be at a leaf node. It must be a number greater than or "
        "equal to 1.",
        default=1,
        ge=1,
    )
    max_leaf_nodes: Optional[
        int_field(
            description="The 'max_leaf_nodes' parameter must be an integer greater "
            "than or equal to 2.",
            default=None,
            ge=2,
        )
    ]
    random_state: Optional[
        int_field(
            description="The 'random_state' parameter must be an integer greater than "
            "or equal to 0.",
            default=None,
            ge=0,
        )
    ]


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier
):
    """Scikit-learn's Random Forest classifier wrapper for DashAI."""

    SCHEMA = RandomForestClassifierSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        super().__init__(**kwargs)
