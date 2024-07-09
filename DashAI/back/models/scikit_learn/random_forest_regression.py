from sklearn.ensemble import RandomForestRegressor as _RandomForestRegressor

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RandomForestRegression(
    RegressionModel, SklearnLikeRegressor, _RandomForestRegressor
):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""
