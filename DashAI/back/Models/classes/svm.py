import json

from Models.classes.numericClassificationModel import NumericClassificationModel
from sklearn.svm import SVC
from Models.classes.sklearnLikeModel import SklearnLikeModel


class SVM(SklearnLikeModel, NumericClassificationModel, SVC):
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    MODEL = "svm"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)
