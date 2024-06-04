from sklearn.svm import LinearSVR as _LinearSVR

from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel


class LinearSVR(RegressionModel, SklearnLikeModel, _LinearSVR):
    """Scikit-learn's Linear Support Vector Regression (LinearSVR)
    wrapper for DashAI."""
