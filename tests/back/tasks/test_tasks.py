import io
import shutil

import pytest
from datasets import DatasetDict
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.tasks.image_classification_task import ImageClassificationTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask


def load_csv_into_datasetdict(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    csv_dataloader = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = csv_dataloader.load_data(
        file=file,
        temp_path="tests/back/tasks",
        params={"separator": ","},
    )
    return datasetdict


def test_validate_tabular_task():
    dataset = to_dashai_dataset(
        load_csv_into_datasetdict("iris.csv"),
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    for split in dataset:
        dataset[split] = dataset[split].change_columns_type(
            column_types={"Species": "Categorical"}
        )
    tabular_task = TabularClassificationTask()

    try:
        tabular_task.validate_dataset_for_task(dataset=dataset, dataset_name="Iris")
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


def test_wrong_type_task():
    dataset = to_dashai_dataset(
        load_csv_into_datasetdict("iris_extra_feature.csv"),
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species", "StemCm"],
    )

    for split in dataset:
        dataset[split] = dataset[split].change_columns_type(
            column_types={"Species": "Categorical"}
        )

    tabular_task = TabularClassificationTask()

    with pytest.raises(TypeError):
        tabular_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="Iris",
        )


def test_prepare_task():
    dataset = to_dashai_dataset(
        load_csv_into_datasetdict("iris.csv"),
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )
    tabular_task = TabularClassificationTask()
    dataset = tabular_task.prepare_for_task(dataset)
    try:
        tabular_task.validate_dataset_for_task(dataset=dataset, dataset_name="Iris")
    except Exception as e:
        pytest.fail(f"Unexpected error in test_prepare_task: {repr(e)}")


def test_not_prepared_task():
    dataset = to_dashai_dataset(
        load_csv_into_datasetdict("iris.csv"),
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )
    tabular_task = TabularClassificationTask()

    with pytest.raises(TypeError):
        tabular_task.validate_dataset_for_task(dataset=dataset, dataset_name="Iris")


@pytest.fixture(scope="module", name="text_classification_dataset")
def text_classification_dataset_fixture():
    test_dataset_path = "tests/back/tasks/ImdbSentimentDatasetSmall.json"
    json_dataloader = JSONDataLoader()

    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    dataset = json_dataloader.load_data(
        file=file,
        temp_path="tests/back/tasks",
        params={"data_key": "data"},
    )

    dashai_dataset = to_dashai_dataset(
        dataset,
        inputs_columns=["text"],
        outputs_columns=["class"],
    )

    split_dataset = json_dataloader.split_dataset(
        dashai_dataset,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
        class_column=dataset["train"].outputs_columns[0],
    )
    return split_dataset


def test_validate_text_dataset(text_classification_dataset: DatasetDict):
    text_class_task = TextClassificationTask()
    imbd_sentiment_dataset = text_class_task.prepare_for_task(
        text_classification_dataset
    )
    try:
        text_class_task.validate_dataset_for_task(
            dataset=imbd_sentiment_dataset,
            dataset_name="IMDBDataset",
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


@pytest.fixture(scope="module", name="image_classification_dataset")
def image_classification_dataset_fixture():
    test_dataset_path = "tests/back/tasks/beans_dataset_small.zip"
    image_dataloader = ImageDataLoader()

    with open(test_dataset_path, "rb") as file:
        upload_file = UploadFile(
            file=file,
            filename=test_dataset_path,
            headers=Headers({"Content-Type": "application/zip"}),
        )
        dataset_dict = image_dataloader.load_data(
            file=upload_file,
            params={},
            temp_path="tests/back/tasks/beans_dataset",
        )

    dataset = to_dashai_dataset(
        dataset_dict, inputs_columns=["image"], outputs_columns=["label"]
    )
    split_dataset = image_dataloader.split_dataset(
        dataset,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
        class_column=dataset["train"].outputs_columns[0],
    )

    yield split_dataset
    shutil.rmtree("tests/back/tasks/beans_dataset", ignore_errors=True)


def test_validate_image_class_task(image_classification_dataset):
    image_class_task = ImageClassificationTask()
    dataset = image_class_task.prepare_for_task(image_classification_dataset)
    try:
        image_class_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="Beans Dataset",
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


@pytest.fixture(scope="module", name="translation_dataset")
def translation_dataset_fixture():
    test_dataset_path = "tests/back/tasks/translationEngSpaDatasetSmall.json"
    json_dataloader = JSONDataLoader()

    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(json_binary)

    dataset = json_dataloader.load_data(
        file=file,
        temp_path="tests/back/tasks",
        params={"data_key": "data"},
    )

    dataset = to_dashai_dataset(
        dataset, inputs_columns=["text"], outputs_columns=["class"]
    )

    split_dataset = json_dataloader.split_dataset(
        dataset,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
        class_column=dataset["train"].outputs_columns[0],
    )
    return split_dataset


def test_validate_translation_task(translation_dataset):
    translation_task = TranslationTask()
    dataset = translation_task.prepare_for_task(translation_dataset)
    try:
        translation_task.validate_dataset_for_task(
            dataset=dataset, dataset_name="EngSpaDataset"
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")
