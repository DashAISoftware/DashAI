import json

from Models.classes.numericClassificationModel import NumericClassificationModel
from Models.classes.sklearnLikeModel import SklearnLikeModel
from sklearn.ensemble import RandomForestClassifier


class RandomForest(
    SklearnLikeModel, NumericClassificationModel, RandomForestClassifier
):
    """ """

    MODEL = "randomforest"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
