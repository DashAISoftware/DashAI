import json

from sklearn.svm import SVC as _SVC

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SVC(TabularClassificationModel, SklearnLikeModel, _SVC):
    """Scikit-learn's Support Vector Machine (SVM) classifier wrapper for DashAI."""

    MODEL = "SVC"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self):
        super().__init__(probability=True)
