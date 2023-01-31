import json

from models.sklearn.sklearn_model import SklearnLikeModel
from models.tabular_classification_model import TabularClassificationModel
from sklearn.neighbors import KNeighborsClassifier as SklearnKNeighborsClassifier


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, SklearnKNeighborsClassifier
):
    """
    K Nearest Neighbors is a supervized classification method,
    that determines the probability that an element belongs to
    a certain class, considering its k nearest neighbors.
    """

    MODEL = "knn"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
