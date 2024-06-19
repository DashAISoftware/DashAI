from sklearn.dummy import DummyClassifier as _DummyClassifier

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DummyClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _DummyClassifier
):
    """Scikit-learn's DummyClassifier wrapper for DashAI."""
