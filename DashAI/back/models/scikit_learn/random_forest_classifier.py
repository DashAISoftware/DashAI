import json

from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier
):
    """Scikit-learn's Random Forest classifier wrapper for DashAI."""

    @classmethod
    def get_schema(cls):
        with open(
            "DashAI/back/models/parameters/models_schemas/RandomForestClassifier.json"
        ) as f:
            cls.SCHEMA = json.load(f)
