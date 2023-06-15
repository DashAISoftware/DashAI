import io
import shutil
import zipfile

import pytest
from datasets import load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.tasks.image_classification_task import ImageClassificationTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask


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
    test_dataset_path = "tests/back/tasks/ImdbSentimentDataset.json"
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
    yield separate_datasetdict


def test_create_text_task():
    try:
        TextClassificationTask.create()
    except Exception as e:
        pytest.fail(f"Unexpected error in test_create_tabular_task: {repr(e)}")


def test_validate_text_class_task(load_text_dashaidataset):
    text_class_task = TextClassificationTask.create()
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
    zip_filename = "tests/back/tasks/beans_dataset.zip"
    destination_folder = "tests/back/tasks/beans_dataset"
    with zipfile.ZipFile(zip_filename, "r") as zip_ref:
        zip_ref.extractall(destination_folder)
    datasetdict = load_dataset("imagefolder", data_dir=destination_folder)
    inputs_columns = ["image"]
    outputs_columns = ["label"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    yield datasetdict
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


@pytest.fixture(scope="module", name="load_translation_dashaidataset")
def fixture_load_translation_dashaidataset():
    test_dataset_path = "tests/back/tasks/translationEngSpaDataset.json"
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
    yield separate_datasetdict


def test_create_translation_task():
    try:
        TranslationTask.create()
    except Exception as e:
        pytest.fail(f"Unexpected error in test_create_tabular_task: {repr(e)}")


def test_validate_translation_task(load_translation_dashaidataset):
    translation_task = TranslationTask.create()
    name_datasetdict = "EngSpaDataset"
    load_translation_dashaidataset = translation_task.prepare_for_task(
        load_translation_dashaidataset
    )
    try:
        translation_task.validate_dataset_for_task(
            load_translation_dashaidataset, name_datasetdict
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")
