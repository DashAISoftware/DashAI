import pytest
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from starlette.datastructures import UploadFile
import io


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
    dataset = dataloader_test.load_data("tests/back/dataloaders", params, file=file)
    yield [dataset, dataloader_test]


def test_inputs_outputs_columns(dataset_created: list):
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    dataset = dataset_created[1].to_dataset_dashai(
        dataset_created[0], inputs_columns, outputs_columns
    )
    assert dataset["train"].inputs_columns == inputs_columns
    assert dataset["train"].outputs_columns == outputs_columns


def test_wrong_size_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = [
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ]
        outputs_columns = ["Species", "SepalWidthCm"]
        dataset = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_undefined_inputs_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True


def test_wrong_name_outputs_columns(dataset_created: list):
    with pytest.raises(ValueError):
        inputs_columns = ["Sepal", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        outputs_columns = ["Species"]
        dataset = dataset_created[1].to_dataset_dashai(
            dataset_created[0], inputs_columns, outputs_columns
        )
    assert True
