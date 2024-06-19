from sklearn.tree import DecisionTreeClassifier as _DecisionTreeClassifier

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DecisionTreeClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _DecisionTreeClassifier
):
    """Scikit-learn's Decision Tree Classifier wrapper for DashAI."""
