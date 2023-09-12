from sklearn.ensemble import (
    HistGradientBoostingClassifier as _HistGradientBoostingClassifier,
)

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class HistGradientBoostingClassifier(
    TabularClassificationModel, SklearnLikeModel, _HistGradientBoostingClassifier
):
    """Scikit-learn's HistGradientBoostingRegressor wrapper for DashAI."""
