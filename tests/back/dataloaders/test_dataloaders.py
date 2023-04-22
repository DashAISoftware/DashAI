import pytest
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from datasets.builder import DatasetGenerationError
from starlette.datastructures import UploadFile
import io
from datasets import DatasetDict, Dataset
from pyarrow.lib import ArrowInvalid


### RUTA: pytest tests/back/dataloaders/test_dataloaders.py

# def test_foo():
#     test_dataset_path = "iris.csv"
#     dataloader_test = CSVDataLoader()
#     dataloader_test.load_data(test_dataset_path, {"a": 2})
#     print(test_dataset_path)
#     assert False

import os

def test_csv_dataloader_to_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, 'r') as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
    file = UploadFile(csv_binary)
    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert isinstance(dataset, DatasetDict)


def test_wrong_create_csv_dataloader():
    with pytest.raises(ValueError):
        test_dataset_path = "tests/back/dataloaders/iris.csv"
        dataloader_test = CSVDataLoader()
        params = {"separato": ","}
        with open(test_dataset_path, 'r') as file:
            csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
        file = UploadFile(csv_binary)
        dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert True

def test_wrong_path_create_csv_dataloader():
    with pytest.raises(FileNotFoundError):
        test_dataset_path = "tests/back/dataloaders/iris_unexisted.csv"
        dataloader_test = CSVDataLoader()
        params = {"separator": ","}
        with open(test_dataset_path, 'r') as file:
            csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
        file = UploadFile(csv_binary)
        dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert True

# Algunas cosas si hay ejemplos con mas de las columnas es error, si hay
# vacios en las columnas lo pone como None, siempre se trata de inferir
# los tipos, se suele poner en string en caso de incompatbilidad
def test_invalidate_csv_dataloader():
    with pytest.raises(DatasetGenerationError):
        test_dataset_path = "tests/back/dataloaders/wrong_iris.csv"
        dataloader_test = CSVDataLoader()
        params = {"separator": ","}
        with open(test_dataset_path, 'r') as file:
            csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
        file = UploadFile(csv_binary)
        dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    assert True

@pytest.fixture(scope="module", name="dataset_created")
def fixture_dataset():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, 'r') as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
    file = UploadFile(csv_binary)
    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    yield [dataset, dataloader_test]


def test_inputs_outputs_columns(dataset_created: list):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    dataset = dataset_created[1].select_inputs_outputs_columns(dataset_created[0], inputs_columns, outputs_columns)
    assert dataset["train"].inputs_columns == inputs_columns
    assert dataset["train"].outputs_columns == outputs_columns

def test_wrong_size_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species", "SepalWidthCm"]
        dataset = dataset_created[1].select_inputs_outputs_columns(dataset_created[0], inputs_columns, outputs_columns)
    assert True

def test_undefined_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset = dataset_created[1].select_inputs_outputs_columns(dataset_created[0], inputs_columns, outputs_columns)
    assert True

def test_wrong_name_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset = dataset_created[1].select_inputs_outputs_columns(dataset_created[0], inputs_columns, outputs_columns)
    assert True

@pytest.fixture(scope="module", name="datasetdashai_created")
def fixture_datasetdashai():
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, 'r') as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding='utf8'))
    file = UploadFile(csv_binary)
    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    dataset = dataloader_test.select_inputs_outputs_columns(dataset, inputs_columns, outputs_columns)
    yield [dataset, dataloader_test]

def test_wrong_name_column(datasetdashai_created: list):
    with pytest.raises(ValueError):
        tipos = {"Speci": "Categorico"}
        dataset = datasetdashai_created[1].change_columns_type(datasetdashai_created[0], tipos)
    assert True

def test_wrong_type_column(datasetdashai_created: list):
    with pytest.raises(ArrowInvalid):
        tipos = {"Species": "Numerico"}
        dataset = datasetdashai_created[1].change_columns_type(datasetdashai_created[0], tipos)
    assert True

def test_datasetdashai_after_cast(datasetdashai_created: list):
    inputs_columns = datasetdashai_created[0]["train"].inputs_columns
    tipos = {"Species": "Categorico"}
    dataset = datasetdashai_created[1].change_columns_type(datasetdashai_created[0], tipos)
    assert dataset["train"].inputs_columns == inputs_columns

