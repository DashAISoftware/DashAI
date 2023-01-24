import json

from Models.classes.numericClassificationModel import NumericClassificationModel
from Models.classes.sklearnLikeModel import SkleanLikeModel
from sklearn.ensemble import RandomForestClassifier


class RandomForest(SkleanLikeModel, NumericClassificationModel, RandomForestClassifier):
    """ """

    MODEL = "randomforest"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
