from sklearn.neural_network import MLPRegressor as _MLPregressor

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class MLPRegression(RegressionModel, SklearnLikeRegressor, _MLPregressor):
    """Scikit-learn's MLP Regression wrapper for DashAI."""
