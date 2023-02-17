import json

from models.sklearn.sklearn_model import SklearnModel
from models.tabular_classification_model import TabularClassificationModel
from sklearn.svm import SVC as _SVC


class SVC(SklearnModel, TabularClassificationModel, _SVC):
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    MODEL = "SVC"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
