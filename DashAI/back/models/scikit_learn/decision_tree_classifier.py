from sklearn.tree import DecisionTreeClassifier as _DecisionTreeClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DecisionTreeClassifier(
    TabularClassificationModel, SklearnLikeModel, _DecisionTreeClassifier
):
    """Scikit-learn's Decision Tree Classifier wrapper for DashAI."""
