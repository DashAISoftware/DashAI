import json

from sklearn.svm import SVC

from DashAI.back.models.classes.sklearn_like_model import SkleanLikeModel
from DashAI.back.models.classes.tabular_classification_model import (
    TabularClassificationModel,
)


class SVM(SkleanLikeModel, TabularClassificationModel, SVC):
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    MODEL = "svm"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
