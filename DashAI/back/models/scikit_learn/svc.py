import json

from sklearn.svm import SVC as _SVC

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SVC(TabularClassificationModel, SklearnLikeModel, _SVC):
    """
    Scikit-learn's Support Vector Machine (SVM) classifier wrapper for DashAI.
    """

    @classmethod
    def get_schema(cls):
        with open("DashAI/back/models/parameters/models_schemas/SVC.json") as f:
            cls.SCHEMA = json.load(f)
        return cls.SCHEMA

    def __init__(self):
        super().__init__(probability=True)
