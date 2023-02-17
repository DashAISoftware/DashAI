import json

from models.sklearn.sklearn_model import SklearnModel
from models.tabular_classification_model import TabularClassificationModel
from sklearn.svm import SVC as _SVC


class SVC(TabularClassificationModel, _SVC): # Tabular Classification ya hereda de SklearnModel
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    _compatible_tasks = ["TabularClassificationTask"]
    MODEL = "svm"
    with open(f"models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

def get_class():
    return SVC