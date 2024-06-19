from sklearn.linear_model import Ridge as _Ridge

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RidgeRegression(RegressionModel, SklearnLikeRegressor, _Ridge):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""
