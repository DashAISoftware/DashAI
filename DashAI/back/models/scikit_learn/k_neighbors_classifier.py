from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _KNeighborsClassifier
):
    """Scikit-learn's K-Nearest Neighbors (KNN) classifier wrapper for DashAI."""
