import json

from sklearn.neighbors import KNeighborsClassifier

from DashAI.back.models.classes.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.classes.tabular_classification_model import (
    TabularClassificationModel,
)


class KNN(SklearnLikeModel, TabularClassificationModel, KNeighborsClassifier):
    """
    K Nearest Neighbors is a supervized classification method,
    that determines the probability that an element belongs to
    a certain class, considering its k nearest neighbors.
    """

    MODEL = "knn"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
