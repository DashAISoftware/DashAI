import json

from sklearn.ensemble import RandomForestClassifier

from DashAI.back.models.classes.sklearn_like_model import SkleanLikeModel
from DashAI.back.models.classes.tabular_classification_model import (
    TabularClassificationModel,
)


class RandomForest(SkleanLikeModel, TabularClassificationModel, RandomForestClassifier):
    """ """

    MODEL = "randomforest"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
