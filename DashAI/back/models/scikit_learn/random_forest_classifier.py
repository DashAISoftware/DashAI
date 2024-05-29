from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    optimizer_int_field,
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
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 100,
            "lower_bound": 50,
            "upper_bound": 200,
        },
        description="The 'n_estimators' parameter corresponds to the number of "
        "decision trees. It must be an integer greater than or equal to 1.",
    )  # type: ignore
    max_depth: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 10,
        },
        description="The 'max_depth' parameter corresponds to the maximum depth of "
        "the tree. It must be an integer greater than or equal to 1.",
    )  # type: ignore
    min_samples_split: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 10,
        },
        description="The 'min_samples_split' parameter is the minimum number of "
        "samples required to split an internal node. It must be a number greater than "
        "or equal to 2.",
    )  # type: ignore
    min_samples_leaf: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1,
            "lower_bound": 1,
            "upper_bound": 10,
        },
        description="The 'min_samples_leaf' parameter is the minimum number of "
        "samples required to be at a leaf node. It must be a number greater than or "
        "equal to 1.",
    )  # type: ignore
    max_leaf_nodes: schema_field(
        optimizer_int_field(ge=2),
        placeholder={
            "optimize": False,
            "fixed_value": 2,
            "lower_bound": 2,
            "upper_bound": 10,
        },
        description="The 'max_leaf_nodes' parameter must be an integer greater "
        "than or equal to 2.",
    )  # type: ignore
    random_state: schema_field(
        optimizer_int_field(ge=0),
        placeholder=None,
        description="The 'random_state' parameter must be an integer greater than "
        "or equal to 0.",
    )  # type: ignore
    random_state: schema_field(
        optimizer_int_field(ge=0),
        placeholder={
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 0,
            "upper_bound": 10,
        },
        description="The 'random_state' parameter must be an integer greater than "
        "or equal to 0.",
    )  # type: ignore


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier
):
    """Scikit-learn's Random Forest classifier wrapper for DashAI."""

    SCHEMA = RandomForestClassifierSchema

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
