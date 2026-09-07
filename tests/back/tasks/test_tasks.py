import os
import pathlib

import PIL
import pytest
from datasets import DatasetDict

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    split_dataset,
    split_indexes,
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.dependencies.database.models import ProcessData
from DashAI.back.tasks.controlnet_task import ControlNetTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.text_to_image_generation_task import TextToImageGenerationTask
from DashAI.back.tasks.text_to_text_generation_task import TextToTextGenerationTask
from DashAI.back.tasks.translation_task import TranslationTask


def load_csv_into_datasetdict_iris(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    csv_dataloader = CSVDataLoader()

    datasetdict = csv_dataloader.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path="tests/back/tasks",
        params={"separator": ","},
    )
    schema = {
        "SepalLengthCm": {"type": "Float", "dtype": "float64"},
        "SepalWidthCm": {"type": "Float", "dtype": "float64"},
        "PetalLengthCm": {"type": "Float", "dtype": "float64"},
        "PetalWidthCm": {"type": "Float", "dtype": "float64"},
        "Species": {"type": "Categorical", "dtype": "string"},
    }
    datasetdict = transform_dataset_with_schema(datasetdict, schema)
    return datasetdict


def load_csv_into_datasetdict_iris_extra(file_name):
    test_dataset_path = f"tests/back/tasks/{file_name}"
    csv_dataloader = CSVDataLoader()

    datasetdict = csv_dataloader.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path="tests/back/tasks",
        params={"separator": ","},
    )
    schema = {
        "SepalLengthCm": {"type": "Float", "dtype": "float64"},
        "SepalWidthCm": {"type": "Float", "dtype": "float64"},
        "PetalLengthCm": {"type": "Float", "dtype": "float64"},
        "PetalWidthCm": {"type": "Float", "dtype": "float64"},
        "Species": {"type": "Categorical", "dtype": "string"},
        "StemCm": {"type": "Float", "dtype": "float64"},
    }
    datasetdict = transform_dataset_with_schema(datasetdict, schema)
    return datasetdict


def test_validate_tabular_task():
    dataset = to_dashai_dataset(load_csv_into_datasetdict_iris("iris.csv"))

    tabular_task = TabularClassificationTask()
    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species"]
    try:
        tabular_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="Iris",
            input_columns=inputs_columns,
            output_columns=outputs_columns,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


def test_wrong_type_task():
    dataset = to_dashai_dataset(
        load_csv_into_datasetdict_iris_extra("iris_extra_feature.csv")
    )

    tabular_task = TabularClassificationTask()

    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species", "StemCm"]
    with pytest.raises(TypeError):
        tabular_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="Iris",
            input_columns=inputs_columns,
            output_columns=outputs_columns,
        )


def test_prepare_task():
    dataset = to_dashai_dataset(load_csv_into_datasetdict_iris("iris.csv"))
    tabular_task = TabularClassificationTask()
    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species"]
    dataset = tabular_task.prepare_for_task(dataset, inputs_columns, outputs_columns)
    try:
        tabular_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="Iris",
            input_columns=inputs_columns,
            output_columns=outputs_columns,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_prepare_task: {repr(e)}")


def test_get_tabular_class_task_metadata():
    tabular_class_task = TabularClassificationTask()
    metadata = tabular_class_task.get_metadata()

    assert len(metadata.keys()) == 4
    assert metadata["inputs_types"] == ["Float", "Integer", "Categorical"]
    assert metadata["outputs_types"] == ["Categorical"]
    assert metadata["inputs_cardinality"] == "n"
    assert metadata["outputs_cardinality"] == 1


@pytest.fixture(scope="module", name="text_classification_dataset")
def text_classification_dataset_fixture():
    test_dataset_path = "tests/back/tasks/ImdbSentimentDatasetSmall.json"
    json_dataloader = JSONDataLoader()

    dataset = json_dataloader.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path="tests/back/tasks",
        params={
            "data_key": "data",
        },
    )
    schema = {
        "text": {"type": "Text", "dtype": "string"},
        "class": {"type": "Categorical", "dtype": "int32"},
    }
    dashai_dataset = transform_dataset_with_schema(dataset, schema)

    total_rows = dashai_dataset.num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_datasetdict = split_dataset(
        dashai_dataset,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return split_datasetdict


def test_validate_text_dataset(text_classification_dataset: DatasetDict):
    text_class_task = TextClassificationTask()
    inputs_columns = ["text"]
    outputs_columns = ["class"]
    imbd_sentiment_dataset = text_class_task.prepare_for_task(
        text_classification_dataset, inputs_columns, outputs_columns
    )
    try:
        text_class_task.validate_dataset_for_task(
            dataset=imbd_sentiment_dataset,
            dataset_name="IMDBDataset",
            input_columns=inputs_columns,
            output_columns=outputs_columns,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


def test_get_text_class_task_metadata():
    text_class_task = TextClassificationTask()
    metadata = text_class_task.get_metadata()

    assert len(metadata.keys()) == 4
    assert metadata["inputs_types"] == ["Text"]
    assert metadata["outputs_types"] == ["Categorical"]
    assert metadata["inputs_cardinality"] == 1
    assert metadata["outputs_cardinality"] == 1


@pytest.fixture(scope="module", name="translation_dataset")
def translation_dataset_fixture():
    test_dataset_path = "tests/back/tasks/translationEngSpaDatasetSmall.json"
    json_dataloader = JSONDataLoader()

    dataset = json_dataloader.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path="tests/back/tasks",
        params={"data_key": "data"},
    )

    schema = {
        "text": {"type": "Text", "dtype": "string"},
        "class": {"type": "Text", "dtype": "string"},
    }
    dataset = transform_dataset_with_schema(dataset, schema)

    dataset = to_dashai_dataset(dataset)

    total_rows = dataset.num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_datasetdict = split_dataset(
        dataset,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )
    return split_datasetdict


def test_validate_translation_task(translation_dataset):
    translation_task = TranslationTask()
    inputs_columns = ["text"]
    outputs_columns = ["class"]
    dataset = translation_task.prepare_for_task(
        translation_dataset, inputs_columns, outputs_columns
    )
    try:
        translation_task.validate_dataset_for_task(
            dataset=dataset,
            dataset_name="EngSpaDataset",
            input_columns=inputs_columns,
            output_columns=outputs_columns,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_validate_task: {repr(e)}")


def test_get_translation_task_metadata():
    translation_task = TranslationTask()
    metadata = translation_task.get_metadata()

    assert len(metadata.keys()) == 4
    assert metadata["inputs_types"] == ["Text"]
    assert metadata["outputs_types"] == ["Text"]
    assert metadata["inputs_cardinality"] == 1
    assert metadata["outputs_cardinality"] == 1


# Generative tasks
@pytest.fixture(scope="module", name="sample_image")
def sample_image_fixture():
    return PIL.Image.new("RGB", (256, 256), color=(255, 255, 255))


@pytest.fixture(scope="module", name="temp_path")
def temp_path_fixture():
    temp_path = pathlib.Path("tests") / "back" / "tasks" / "temp"
    os.makedirs(temp_path, exist_ok=True)
    yield temp_path
    # Cleanup after all tests in the module using this fixture have finished
    if temp_path.exists() and temp_path.is_dir():
        for root, dirs, files in os.walk(temp_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_path)


# Text To Text Generation Task
def test_get_text_to_text_task_metadata():
    text_to_text_task = TextToTextGenerationTask()
    metadata = text_to_text_task.get_metadata()

    assert metadata == {
        "inputs": {"str": {"min": 1, "max": 1}},
        "outputs": {"str": {"min": 1, "max": 1}},
        "entry_point": "generic",
    }


def test_prepare_for_task_text_to_text():
    text_to_text_task = TextToTextGenerationTask()
    input_data = [ProcessData(data="What is the capital of France?")]

    prepared = text_to_text_task.prepare_for_task(input_data)

    expected = [
        {"role": "user", "content": "What is the capital of France?"},
    ]
    assert prepared == expected


def test_prepare_for_task_text_to_text_with_history():
    text_to_text_task = TextToTextGenerationTask()
    input_data = [ProcessData(data="What is the capital of France?")]
    history = [("What is the capital of Spain?", "Madrid")]

    prepared = text_to_text_task.prepare_for_task(input_data, history=history)

    expected = [
        {"role": "user", "content": "What is the capital of Spain?"},
        {"role": "assistant", "content": "Madrid"},
        {"role": "user", "content": "What is the capital of France?"},
    ]
    assert prepared == expected


def prepare_input_for_database_text_to_text():
    text_to_text_task = TextToTextGenerationTask()
    input_data = ["What is the capital of France?"]
    prepared_input = text_to_text_task.prepare_input_for_database(input_data)

    assert prepared_input == input_data


def process_output_text_to_text():
    text_to_text_task = TextToTextGenerationTask()
    output_data = ["Paris is the capital of France."]
    processed_output = text_to_text_task.process_output(output_data)

    assert processed_output == output_data


def process_input_from_database_text_to_text():
    text_to_text_task = TextToTextGenerationTask()
    input_data = ["What is the capital of France?"]
    processed_input = text_to_text_task.process_input(input_data)

    assert processed_input == input_data


# Text To Image Generation Task
def test_get_text_to_image_task_metadata():
    text_to_image_task = TextToImageGenerationTask()
    metadata = text_to_image_task.get_metadata()

    assert metadata == {
        "inputs": {"str": {"min": 1, "max": 1}},
        "outputs": {"Image": {"min": 1, "max": "n"}},
        "entry_point": "generic",
    }


def test_prepare_for_task_text_to_image():
    text_to_image_task = TextToImageGenerationTask()
    input_data = [ProcessData(data="A beautiful landscape")]
    prepared_input = text_to_image_task.prepare_for_task(input_data)

    assert prepared_input == "A beautiful landscape"


def test_input_for_database_text_to_image():
    text_to_image_task = TextToImageGenerationTask()
    input_data = ["A beautiful landscape"]
    prepared_input = text_to_image_task.prepare_input_for_database(input_data)

    assert isinstance(prepared_input, list)
    assert isinstance(prepared_input[0][0], str)
    assert prepared_input[0][1] == "str"


def test_process_output_text_to_image(sample_image, temp_path):
    text_to_image_task = TextToImageGenerationTask()
    output_data = [sample_image]
    processed_output = text_to_image_task.process_output(
        output_data, images_path=temp_path
    )

    assert isinstance(processed_output, list)
    assert all(isinstance(img[0], str) for img in processed_output)
    assert all(img[1] == "Image" for img in processed_output)
    # Check if the image is saved in the temp path
    assert len(os.listdir(temp_path)) == 1


def test_process_output_from_database_text_to_image():
    text_to_image_task = TextToImageGenerationTask()
    output_data = [
        ProcessData(data="dir/sample_image_0.png"),
        ProcessData(data="dir/sample_image_1.png"),
    ]
    processed_output = text_to_image_task.process_output_from_database(output_data)

    assert isinstance(processed_output, list)
    assert all(isinstance(p.data, str) for p in processed_output)
    assert len(processed_output) == 2
    assert processed_output[0].data == "sample_image_0.png"
    assert processed_output[1].data == "sample_image_1.png"


def test_process_input_from_database_text_to_image():
    text_to_image_task = TextToImageGenerationTask()
    input_data = ["A beautiful landscape"]
    processed_input = text_to_image_task.process_input_from_database(input_data)

    assert processed_input == input_data


# ControlNet Task
def test_get_controlnet_task_metadata():
    controlnet_task = ControlNetTask()
    metadata = controlnet_task.get_metadata()

    assert metadata == {
        "inputs": {
            "Image": {"min": 1, "max": 1},
            "str": {"min": 1, "max": 1},
        },
        "outputs": {"Image": {"min": 1, "max": "n"}},
        "entry_point": "generic",
    }


def test_prepare_for_task_controlnet(sample_image, temp_path):
    controlnet_task = ControlNetTask()
    path_image = temp_path / "sample_controlnet_image.png"
    sample_image.save(path_image)

    input_data = [
        ProcessData(data=path_image, data_type="Image"),
        ProcessData(data="A beautiful landscape", data_type="str"),
    ]

    prepared_input = controlnet_task.prepare_for_task(input_data)

    assert isinstance(prepared_input, tuple)
    assert isinstance(prepared_input[0], PIL.Image.Image)
    assert isinstance(prepared_input[1], str)


def test_prepare_input_for_database_controlnet(sample_image, temp_path):
    controlnet_task = ControlNetTask()

    bytes_image = sample_image.tobytes()

    input_data = [bytes_image, "A beautiful landscape"]
    prepared_input = controlnet_task.prepare_input_for_database(
        input_data, images_path=temp_path / "controlnet_prepare_for_database"
    )

    assert isinstance(prepared_input, list)
    assert isinstance(prepared_input[0][0], str)
    assert isinstance(prepared_input[1][0], str)
    assert prepared_input[0][1] == "Image"
    assert prepared_input[1][1] == "str"

    assert prepared_input[1][0] == "A beautiful landscape"
    # Check if the image is saved in the temp path
    assert len(os.listdir(temp_path / "controlnet_prepare_for_database")) == 1


def test_process_output_controlnet(sample_image, temp_path):
    controlnet_task = ControlNetTask()
    output_data = [sample_image]
    processed_output = controlnet_task.process_output(
        output_data, images_path=temp_path / "controlnet_process_output"
    )

    assert isinstance(processed_output, list)
    assert all(isinstance(img[0], str) for img in processed_output)
    assert all(img[1] == "Image" for img in processed_output)
    # Check if the image is saved in the temp path
    assert len(os.listdir(temp_path / "controlnet_process_output")) == 1


def test_process_output_from_database_controlnet():
    controlnet_task = ControlNetTask()
    output_data = [
        ProcessData(data="dir/sample_image_0.png"),
        ProcessData(data="dir/sample_image_1.png"),
    ]
    processed_output = controlnet_task.process_output_from_database(output_data)

    assert isinstance(processed_output, list)
    assert all(isinstance(img.data, str) for img in processed_output)
    assert len(processed_output) == 2
    assert processed_output[0].data == "sample_image_0.png"
    assert processed_output[1].data == "sample_image_1.png"
