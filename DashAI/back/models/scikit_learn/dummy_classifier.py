from sklearn.dummy import DummyClassifier as _DummyClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DummyClassifier(TabularClassificationModel, SklearnLikeModel, _DummyClassifier):
    """Scikit-learn's DummyClassifier wrapper for DashAI."""
