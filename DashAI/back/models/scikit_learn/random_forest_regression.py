from sklearn.ensemble import RandomForestRegressor as _RFRegressor

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class RandomForestRegression(RegressionModel, SklearnLikeRegressor, _RFRegressor):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""
