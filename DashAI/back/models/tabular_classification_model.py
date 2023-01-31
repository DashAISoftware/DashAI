from models.sklearn.sklearn_model import SklearnModel


class TabularClassificationModel(SklearnModel):
    compatible_tasks = ["TabularClassificationTasks"]
