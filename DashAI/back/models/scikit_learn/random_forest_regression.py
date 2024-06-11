from sklearn.linear_model import RandomForestRegressor as _RFRegressor

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel


class RandomForestRegression(RegressionModel, SklearnLikeModel, _RFRegressor):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""
