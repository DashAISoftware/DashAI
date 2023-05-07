import pytest
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from starlette.datastructures import UploadFile
from pyarrow.lib import ArrowInvalid
import io
from datasets import DatasetDict


@pytest.fixture(scope="module", name="dataset_created")
def fixture_dataset():
    # Create DatasetDict from csv
    test_dataset_path = "tests/back/dataloaders/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    yield [datasetdict, dataloader_test]


def test_inputs_outputs_columns(dataset_created: list):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = dataset_created[1].to_dataset_dashai(
        dataset_created[0], inputs_columns, outputs_columns
    )
    assert datasetdict["train"].inputs_columns == inputs_columns
    assert datasetdict["train"].outputs_columns == outputs_columns


def test_wrong_size_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = [
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ]
        outputs_columns = ["Species", "SepalWidthCm"]
        datasetdict = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_undefined_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        datasetdict = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_wrong_name_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        datasetdict = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
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
    datasetdict = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = dataloader_test.to_dataset_dashai(
        datasetdict, inputs_columns, outputs_columns
    )
    yield datasetdict

def test_wrong_name_column(datasetdashai_created: DatasetDict):
    with pytest.raises(ValueError):
        tipos = {"Speci": "Categorico"}
        for split in datasetdashai_created:
            datasetdashai_created[split] = datasetdashai_created[split].change_columns_type(tipos)
    assert True

def test_wrong_type_column(datasetdashai_created: DatasetDict):
    with pytest.raises(ArrowInvalid):
        tipos = {"Species": "Numerico"}
        for split in datasetdashai_created:
            datasetdashai_created[split] = datasetdashai_created[split].change_columns_type(tipos)
    assert True

def test_datasetdashai_after_cast(datasetdashai_created: DatasetDict):
    inputs_columns = datasetdashai_created["train"].inputs_columns
    tipos = {"Species": "Categorico"}
    for split in datasetdashai_created:
        datasetdashai_created[split] = datasetdashai_created[split].change_columns_type(tipos)
    assert datasetdashai_created["train"].inputs_columns == inputs_columns
