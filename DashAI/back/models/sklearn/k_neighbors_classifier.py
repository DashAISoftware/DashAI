import json

from models.sklearn.sklearn_model import SklearnModel
from models.tabular_classification_model import TabularClassificationModel
from sklearn.neighbors import KNeighborsClassifier as SklearnKNeighborsClassifier


class KNeighborsClassifier(
    TabularClassificationModel, SklearnModel, SklearnKNeighborsClassifier
):
    """
    K Nearest Neighbors is a supervized classification method,
    that determines the probability that an element belongs to
    a certain class, considering its k nearest neighbors.
    """

    _compatible_tasks = ["TabularClassificationTask"] # Shouldn't it be written in Upper case?
    MODEL = "knn"
    with open(f"models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
