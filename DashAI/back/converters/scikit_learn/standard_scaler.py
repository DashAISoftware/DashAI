from sklearn.preprocessing import StandardScaler as StandardScalerOperation
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class StandardScaler(StandardScalerOperation, SklearnLikeConverter):
    """Scikit-learn's Standard Scaler wrapper for DashAI."""