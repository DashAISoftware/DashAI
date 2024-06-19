from sklearn.svm import SVC as _SVC

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SVC(TabularClassificationModel, SklearnLikeClassifier, _SVC):
    """Scikit-learn's Support Vector Machine (SVM) classifier wrapper for DashAI."""

    def __init__(self, **kwargs):
        kwargs["probability"] = True
        super().__init__(**kwargs)
