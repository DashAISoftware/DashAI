import io
import shutil

import pytest
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.tasks.image_classification_task import ImageClassificationTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.text_classification_task import TextClassificationTask


def dashaidataset_from_csv(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data("tests/back/tasks", params, file=file)
    return datasetdict


def test_create_tabular_task():
    try:
        TabularClassificationTask.create()
    except Exception as e:
        pytest.fail(f"Unexpected error in test_create_tabular_task: {repr(e)}")


def test_validate_tabular_task():
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


@pytest.fixture(scope="module", name="load_text_dashaidataset")
def fixture_load_text_dashaidataset():
    test_dataset_path = "tests/back/models/ImdbSentimentDatasetSmall.json"
    dataloader_test = JSONDataLoader()
    params = {"data_key": "data"}
    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    datasetdict = dataloader_test.load_data("tests/back/tasks", params, file=file)
    inputs_columns = ["text"]
    outputs_columns = ["class"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )
    return separate_datasetdict


def test_validate_text_class_task(load_text_dashaidataset):
    text_class_task = TextClassificationTask()
    name_datasetdict = "IMDBDataset"
    load_text_dashaidataset = text_class_task.prepare_for_task(load_text_dashaidataset)
    try:
        text_class_task.validate_dataset_for_task(
            load_text_dashaidataset, name_datasetdict
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


@pytest.fixture(scope="module", name="load_image_dashaidataset")
def fixture_load_image_dashaidataset():
    test_dataset_path = "tests/back/tasks/beans_dataset_small.zip"
    dataloader_test = ImageDataLoader()
    header = Headers({"Content-Type": "application/zip"})
    file = open(test_dataset_path, "rb")  # noqa: SIM115
    upload_file = UploadFile(filename=test_dataset_path, file=file, headers=header)
    datasetdict = dataloader_test.load_data(
        "tests/back/tasks/beans_dataset", file=upload_file
    )
    file.close()
    inputs_columns = ["image"]
    outputs_columns = ["label"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )
    yield separate_datasetdict
    shutil.rmtree("tests/back/tasks/beans_dataset", ignore_errors=True)


def test_create_image_task():
    try:
        ImageClassificationTask.create()
    except Exception as e:
        pytest.fail(f"Unexpected error in test_create_tabular_task: {repr(e)}")


def test_validate_image_class_task(load_image_dashaidataset):
    image_class_task = ImageClassificationTask.create()
    name_datasetdict = "Beans Dataset"
    load_text_dashaidataset = image_class_task.prepare_for_task(
        load_image_dashaidataset
    )
    try:
        image_class_task.validate_dataset_for_task(
            load_text_dashaidataset, name_datasetdict
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")
