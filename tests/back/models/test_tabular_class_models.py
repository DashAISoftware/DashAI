import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from DashAI.back.dataloaders.classes.dataset_dashai import DatasetDashAI
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.svc import SVC


@pytest.fixture(scope="module", name="load_datasetdashai")
def fixture_load_datasetdashai():
    paths = {
        "path_train": "tests/back/models/datasetdashai_train",
        "path_val": "tests/back/models/datasetdashai_validation",
        "path_test": "tests/back/models/datasetdashai_test",
    }
    datasetdashai_train = DatasetDashAI.load_from_disk(paths["path_train"])
    datasetdashai_val = DatasetDashAI.load_from_disk(paths["path_val"])
    datasetdashai_test = DatasetDashAI.load_from_disk(paths["path_test"])
    datasetdict_dashai = DatasetDict(
        {
            "train": datasetdashai_train,
            "validation": datasetdashai_val,
            "test": datasetdashai_test,
        }
    )
    yield datasetdict_dashai


def test_fit_models_tabular(load_datasetdashai: DatasetDict):
    knn = KNeighborsClassifier()
    dataset_prepared = knn.format_data(load_datasetdashai)
    knn.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    check_is_fitted(knn)
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_datasetdashai)
    rf.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    check_is_fitted(rf)
    svm = SVC()
    dataset_prepared = svm.format_data(load_datasetdashai)
    svm.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    check_is_fitted(svm)
    assert True


def test_predict_models_tabular(load_datasetdashai: DatasetDict):
    knn = KNeighborsClassifier()
    dataset_prepared = knn.format_data(load_datasetdashai)
    knn.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    knn.predict(dataset_prepared["x_test"])

    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_datasetdashai)
    rf.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    rf.predict(dataset_prepared["x_test"])

    svm = SVC()
    dataset_prepared = svm.format_data(load_datasetdashai)
    svm.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    svm.predict(dataset_prepared["x_test"])
    assert True


def test_not_fitted_models_tabular(load_datasetdashai: DatasetDict):
    with pytest.raises(NotFittedError):
        knn = KNeighborsClassifier()
        dataset_prepared = knn.format_data(load_datasetdashai)
        knn.predict(dataset_prepared["x_test"])
    assert True


def test_save_and_load_model(load_datasetdashai: DatasetDict):
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_datasetdashai)
    rf.fit(dataset_prepared["x_train"], dataset_prepared["y_train"])
    rf.save("tests/back/models/rfmodel")
    model_rf = rf.load("tests/back/models/rfmodel")
    model_rf.predict(dataset_prepared["x_test"])
    assert True
