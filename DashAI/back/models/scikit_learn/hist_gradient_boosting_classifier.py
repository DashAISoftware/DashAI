from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _HistGradientBoostingClassifier
):
    """Scikit-learn's HistGradientBoostingRegressor wrapper for DashAI."""
