from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
    string_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class KNeighborsClassifierSchema(BaseSchema):
    """KNN is a supervised classification method that determines the probability of
    an element belonging to a certain class by considering its k closest neighbors.
    """

    n_neighbors: schema_field(
        int_field(ge=1),
        placeholder=5,
        description="The 'n_neighbors' parameter is the number of neighbors to "
        "consider in each input for classification. It must be an integer greater "
        "than or equal to 1.",
    )  # type: ignore
    weights: schema_field(
        string_field(enum=["uniform", "distance"]),
        placeholder="uniform",
        description="The 'weights' parameter must be 'uniform' or 'distance'.",
    )  # type: ignore
    algorithm: schema_field(
        string_field(enum=["auto", "ball_tree", "kd_tree", "brute"]),
        placeholder="auto",
        description="The 'algorithm' parameter must be 'auto', 'ball_tree', "
        "'kd_tree', or 'brute'.",
    )  # type: ignore


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, _KNeighborsClassifier
):
    """Scikit-learn's K-Nearest Neighbors (KNN) classifier wrapper for DashAI."""

    SCHEMA = KNeighborsClassifierSchema
