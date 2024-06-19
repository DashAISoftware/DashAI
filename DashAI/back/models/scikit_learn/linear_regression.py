from sklearn.linear_model import LinearRegression as _LinearRegression

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class LinearRegression(RegressionModel, SklearnLikeRegressor, _LinearRegression):
    """Scikit-learn's Linear Regression wrapper for DashAI."""
