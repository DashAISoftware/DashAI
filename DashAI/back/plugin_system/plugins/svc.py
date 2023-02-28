import json

#from models.sklearn.sklearn_model import SklearnModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel
from sklearn.svm import SVC as _SVC
#from base.base_model import model_register
#from main import model_register
#from DashAI.back.registries.model_registry import ModelRegistry
from DashAI.back.registries.registration import get_model_registry


class SVC(TabularClassificationModel, _SVC): # Tabular Classification ya hereda de SklearnModel
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    _compatible_tasks = ["TabularClassificationTask"]
    MODEL = "SVC"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

def initialize() -> None:
    get_model_registry().register_model(SVC)

def get_class():
    return SVC