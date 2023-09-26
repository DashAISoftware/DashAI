from sklearn.ensemble import RandomForestRegressor as _RandomForestRegressor

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestRegressor(
    TabularClassificationModel, SklearnLikeModel, _RandomForestRegressor
):
    """Scikit-learn's Random Forest Regressor wrapper DashAI."""
