import json

from sklearn.neighbors import KNeighborsClassifier

from DashAI.back.models.classes.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.classes.tabular_classification_model import (
    TabularClassificationModel,
)


class KNN(SklearnLikeModel, TabularClassificationModel, KNeighborsClassifier):
    """
    K Nearest Neighbors is a supervized classification method,
    that determines the probability that an element belongs to
    a certain class, considering its k nearest neighbors.
    """

    MODEL = "knn"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)


# --- Test for new datasets in models---
if __name__ == "__main__":
    knn = KNN()
    folder_path = "DashAI/back/example_datasets/load_iris_example/dataset"
    dataset = knn.load_data(folder_path, "Species")
    # print(dataset["x_train"])

    knn.dashai_fit(dataset["x_train"], dataset["y_train"])
    score = knn.dashai_score(dataset["x_test"], dataset["y_test"])
    # print(score)
