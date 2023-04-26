import pytest
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import DatasetDashAI
from starlette.datastructures import UploadFile
import io

# RUTA: pytest tests/back/tasks/test_tasks.py


def datasetdashai_from_csv(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, 'r') as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
    file = UploadFile(csv_binary)
    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    return [dataset, dataloader_test]

def test_create_tabular_task():
    tabular_task = TabularClassificationTask.create()
    assert True

# Index_col en CSV?

def test_validate_task():
    datasetdashai_csv_created = datasetdashai_from_csv("iris.csv")
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    dataset = datasetdashai_csv_created[1].select_inputs_outputs_columns(datasetdashai_csv_created[0],
                                                                         inputs_columns, outputs_columns)
    tipos = {"Species": "Categorico"}
    dataset = datasetdashai_csv_created[1].change_columns_type(dataset, tipos)
    tabular_task = TabularClassificationTask.create()
    tabular_task.validate_dataset_for_task(dataset)
    assert True


def test_wrong_cardinality_task():
    with pytest.raises(ValueError):
        datasetdashai_csv_created = datasetdashai_from_csv("iris_extra_feature.csv")
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species", "StemCm"]
        dataset = datasetdashai_csv_created[1].select_inputs_outputs_columns(datasetdashai_csv_created[0],
                                                                             inputs_columns, outputs_columns)
        tipos = {"Species": "Categorico"}
        dataset = datasetdashai_csv_created[1].change_columns_type(dataset, tipos)
        tabular_task = TabularClassificationTask.create()
        tabular_task.validate_dataset_for_task(dataset)
    assert True













