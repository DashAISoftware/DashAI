from sklearn.linear_model import LogisticRegression as _LogisticRegression

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class LogisticRegression(
    TabularClassificationModel, SklearnLikeClassifier, _LogisticRegression
):
    """Scikit-learn's Logistic Regression wrapper for DashAI."""
