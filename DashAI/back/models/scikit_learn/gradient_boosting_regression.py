from sklearn.ensemble import GradientBoostingRegressor as _GBRegressor

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import (
    SklearnLikeRegressor,
)


class GradientBoostingR(RegressionModel, SklearnLikeRegressor, _GBRegressor):
    """Scikit-learn's Ridge Regression wrapper for DashAI."""
