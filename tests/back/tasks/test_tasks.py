import pytest
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from starlette.datastructures import UploadFile
import io


def datasetdashai_from_csv(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, 'r') as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    return [datasetdict, dataloader_test]

def test_create_tabular_task():
    tabular_task = TabularClassificationTask.create()
    assert True


def test_validate_task():
    datasetdashai_csv_created = datasetdashai_from_csv("iris.csv")
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = datasetdashai_csv_created[1].to_dataset_dashai(
        datasetdashai_csv_created[0], inputs_columns, outputs_columns
    )
    tipos = {"Species": "Categorico"}
    for split in datasetdict:
        datasetdict[split] = datasetdict[split].change_columns_type(tipos)
    tabular_task = TabularClassificationTask.create()
    tabular_task.validate_dataset_for_task(datasetdict)
    assert True


def test_wrong_cardinality_task():
    with pytest.raises(ValueError):
        datasetdashai_csv_created = datasetdashai_from_csv("iris_extra_feature.csv")
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species", "StemCm"]
        datasetdict = datasetdashai_csv_created[1].to_dataset_dashai(
            datasetdashai_csv_created[0], inputs_columns, outputs_columns
        )
        tipos = {"Species": "Categorico"}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(tipos)
        tabular_task = TabularClassificationTask.create()
        tabular_task.validate_dataset_for_task(datasetdict)
    assert True
