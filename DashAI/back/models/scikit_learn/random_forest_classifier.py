from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _RandomForestClassifier
):
    """Scikit-learn's Random Forest classifier wrapper for DashAI."""
