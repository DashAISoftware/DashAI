import json

from sklearn.ensemble import RandomForestClassifier

from Models.classes.numericClassificationModel import NumericClassificationModel
from Models.classes.sklearnLikeModel import SkleanLikeModel


class RandomForest(SkleanLikeModel, NumericClassificationModel, RandomForestClassifier):
    """ """

    MODEL = "randomforest"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
