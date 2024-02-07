from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from plugins.tabular_plugin.src.tabular_plugin.tabular_classification_model import (
    TabularClassificationModel,
)


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, _KNeighborsClassifier, ConfigObject
):
    """
    Scikit-learn's K-Nearest Neighbors (KNN) classifier wrapper for DashAI.
    """
