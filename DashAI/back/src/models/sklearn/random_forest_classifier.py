import json

from models.sklearn.sklearn_model import SklearnModel
from models.tabular_classification_model import TabularClassificationModel
from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier


class RandomForestClassifier(
    TabularClassificationModel,
    SklearnModel,
    _RandomForestClassifier,
):
    """ """

    MODEL = "RandomForestClassifier"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
