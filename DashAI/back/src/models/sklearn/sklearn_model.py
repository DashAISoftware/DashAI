from io import BytesIO

import joblib
from base.base_model import BaseModel


class SklearnModel(BaseModel):
    """
    Abstract class to define the way to save sklearn like models.
    """

    def save(self, filename=None):

        if filename is None:
            bytes_container = BytesIO()
            joblib.dump(self, bytes_container)
            bytes_container.seek(0)
            return bytes_container.read()
        else:
            joblib.dump(self, filename)

    @staticmethod
    def load(filename):

        model = joblib.load(filename)
        return model
