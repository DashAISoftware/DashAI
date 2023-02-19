import json

from sklearn.ensemble import RandomForestClassifier

from DashAI.back.models.classes.numeric_classification_model import (
    NumericClassificationModel,
)
from DashAI.back.models.classes.sklearn_like_model import SkleanLikeModel


class RandomForest(SkleanLikeModel, NumericClassificationModel, RandomForestClassifier):
    """ """

    MODEL = "randomforest"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
