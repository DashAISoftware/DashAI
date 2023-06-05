import json

from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, _KNeighborsClassifier
):
    """
    K Nearest Neighbors is a supervized classification method,
    that determines the probability that an element belongs to
    a certain class, considering its k nearest neighbors.
    """

    @classmethod
    def get_schema(cls):
        with open(
            "DashAI/back/models/parameters/models_schemas/KNeighborsClassifier.json"
        ) as f:
            cls.SCHEMA = json.load(f)
