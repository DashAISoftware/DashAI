from sklearn.ensemble import (
    AdaBoostClassifier as _AdaBoostClassifier,
)

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class AdaBoostClassifier(
    TabularClassificationModel, SklearnLikeModel, _AdaBoostClassifier
):
    """Scikit-learn's AdaBoostClassifier wrapper for DashAI."""
