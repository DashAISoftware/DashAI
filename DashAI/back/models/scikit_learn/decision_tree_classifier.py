from typing import Optional

from sklearn.tree import DecisionTreeClassifier as _DecisionTreeClassifier

from DashAI.back.core.schema_fields import BaseSchema, int_field, string_field
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DecisionTreeClassifierSchema(BaseSchema):
    """Decision Trees are a set of are a non-parametric supervised learning method that
    learns simple decision rules (structured as a tree) inferred from the data features.
    """

    criterion: string_field(
        description="The function to measure the quality of a split. Supported "
        "criteria are “gini” for the Gini impurity and “log_loss” and “entropy” both "
        "for the Shannon information gain.",
        default="entropy",
        enum=["entropy", "gini", "log_loss"],
    )
    max_depth: Optional[
        int_field(
            description="The maximum depth of the tree. If None, then nodes are "
            "expanded until all leaves are pure or until all leaves contain less than "
            "min_samples_split samples.",
            default=None,
            ge=1,
        )
    ]
    min_samples_split: int_field(
        description="The minimum number of samples required to split an internal "
        "node.",
        default=1,
        ge=1,
    )
    min_samples_leaf: int_field(
        description="The minimum number of samples required to be at a leaf node.",
        default=1,
        ge=1,
    )
    max_features: Optional[
        string_field(
            description="The number of features to consider when looking for the best "
            "split.",
            default=None,
            enum=["auto", "sqrt", "log2"],
        )
    ]


class DecisionTreeClassifier(
    TabularClassificationModel, SklearnLikeModel, _DecisionTreeClassifier
):
    """Scikit-learn's Decision Tree Classifier wrapper for DashAI."""

    SCHEMA = DecisionTreeClassifierSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        super().__init__(**kwargs)
