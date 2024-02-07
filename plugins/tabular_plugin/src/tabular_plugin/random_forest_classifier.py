from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.config_object import ConfigObject
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from plugins.tabular_plugin.src.tabular_plugin.tabular_classification_model import (
    TabularClassificationModel,
)


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier, ConfigObject
):
    """
    Scikit-learn's Random Forest classifier wrapper for DashAI.
    """
