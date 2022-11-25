from io import BytesIO

import joblib
from Models.classes.model import Model


class SklearnLikeModel(Model):
    """
    Abstract class to define the way to save sklearn like models.
    """

    def save(self, filename):
        """
        Method to save the model in the filename path.
        """
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        """
        Method to load the model from the filename path.
        """
        model = joblib.load(filename)
        return model
