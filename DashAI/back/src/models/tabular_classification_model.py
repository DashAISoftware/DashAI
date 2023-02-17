from models.sklearn.sklearn_model import SklearnModel


class TabularClassificationModel(SklearnModel):
    _compatible_tasks = ["TabularClassificationTask"]
