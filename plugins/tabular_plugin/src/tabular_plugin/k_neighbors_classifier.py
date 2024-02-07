from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier
from tabular_plugin.tabular_classification_model import TabularClassificationModel

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeModel, _KNeighborsClassifier, ConfigObject
):
    """
    Scikit-learn's K-Nearest Neighbors (KNN) classifier wrapper for DashAI.
    """
