import json

from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, _KNeighborsClassifier
):
    """
    Scikit-learn's K-Nearest Neighbors (KNN) classifier wrapper for DashAI.
    """

    @classmethod
    def get_schema(cls):
        with open(
            "DashAI/back/models/parameters/models_schemas/KNeighborsClassifier.json"
        ) as f:
            cls.SCHEMA = json.load(f)
        return cls.SCHEMA
