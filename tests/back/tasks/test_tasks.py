import io

import pytest
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


def dashaidataset_from_csv(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    return datasetdict


def test_create_tabular_task():
    TabularClassificationTask.create()
    assert True


def test_validate_task():
    dashaidataset = dashaidataset_from_csv("iris.csv")
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    name_datasetdict = "Iris"
    datasetdict = to_dashai_dataset(dashaidataset, inputs_columns, outputs_columns)
    tipos = {"Species": "Categorical"}
    for split in datasetdict:
        datasetdict[split] = datasetdict[split].change_columns_type(tipos)
    tabular_task = TabularClassificationTask.create()
    try:
        tabular_task.validate_dataset_for_task(datasetdict, name_datasetdict)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


def test_wrong_type_task():
    dashai_dataset_csv = dashaidataset_from_csv("iris_extra_feature.csv")

    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species", "StemCm"]
    datasetdict = to_dashai_dataset(dashai_dataset_csv, inputs_columns, outputs_columns)
    col_types = {"Species": "Categorical"}

    for split in datasetdict:
        datasetdict[split] = datasetdict[split].change_columns_type(col_types)

    tabular_task = TabularClassificationTask.create()
    name_datasetdict = "Iris"

    with pytest.raises(TypeError):
        tabular_task.validate_dataset_for_task(datasetdict, name_datasetdict)


def test_prepare_task():
    datasetdashai_csv_created = dashaidataset_from_csv("iris.csv")
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    name_datasetdict = "Iris"
    datasetdict = to_dashai_dataset(
        datasetdashai_csv_created, inputs_columns, outputs_columns
    )
    tabular_task = TabularClassificationTask.create()
    datasetdict = tabular_task.prepare_for_task(datasetdict)
    try:
        tabular_task.validate_dataset_for_task(datasetdict, name_datasetdict)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_prepare_task: {repr(e)}")


def test_not_prepared_task():
    dashai_dataset_csv = dashaidataset_from_csv("iris.csv")
    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species"]
    name_datasetdict = "Iris"

    datasetdict = to_dashai_dataset(dashai_dataset_csv, inputs_columns, outputs_columns)
    tabular_task = TabularClassificationTask.create()

    with pytest.raises(TypeError):
        tabular_task.validate_dataset_for_task(datasetdict, name_datasetdict)
