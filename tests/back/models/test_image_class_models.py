import shutil
import zipfile

import pytest
from datasets import DatasetDict, load_dataset
from sklearn.exceptions import NotFittedError

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.models.hugging_face.vit_transformer import ViTTransformer
from DashAI.back.tasks.image_classification_task import ImageClassificationTask


# Temporal split
def split_dataset(
    dataset: DatasetDict, train_size: float, val_size: float, test_size: float
):
    assert train_size + val_size + test_size == 1
    val_test_size = 1 - train_size
    val_ratio = val_size / (val_size + test_size)
    train_val_test_datasets = dataset["train"].train_test_split(test_size=val_test_size)
    val_test_datasets = train_val_test_datasets["test"].train_test_split(
        test_size=val_ratio
    )
    dataset["train"] = train_val_test_datasets["train"]
    dataset["validation"] = val_test_datasets["train"]
    dataset["test"] = val_test_datasets["test"]
    return dataset


@pytest.fixture(scope="module", name="load_dashaidataset")
def fixture_load_dashaidataset():
    zip_filename = "tests/back/tasks/beans_dataset.zip"
    destination_folder = "tests/back/tasks/beans_dataset"
    with zipfile.ZipFile(zip_filename, "r") as zip_ref:
        zip_ref.extractall(destination_folder)
    datasetdict = load_dataset("imagefolder", data_dir=destination_folder)
    datasetdict["train"] = datasetdict["train"].select(range(100))
    inputs_columns = ["image"]
    outputs_columns = ["label"]

    separate_datasetdict = split_dataset(
        datasetdict, train_size=0.7, val_size=0.15, test_size=0.15
    )

    separate_datasetdict = to_dashai_dataset(
        separate_datasetdict, inputs_columns, outputs_columns
    )

    text_task = ImageClassificationTask.create()
    separate_datasetdict = text_task.prepare_for_task(separate_datasetdict)
    text_task.validate_dataset_for_task(separate_datasetdict, "beans_dataset")

    yield separate_datasetdict
    shutil.rmtree("tests/back/tasks/beans_dataset", ignore_errors=True)


def test_fit_image_class_model(load_dashaidataset: DatasetDict):
    vit = ViTTransformer()
    vit.fit(load_dashaidataset)
    assert vit.fitted is True


def test_predict_image_class_model(load_dashaidataset: DatasetDict):
    vit = ViTTransformer(num_train_epochs=2, per_device_train_batch_size=32)
    vit.fit(load_dashaidataset)
    pred_vit = vit.predict(load_dashaidataset)
    assert load_dashaidataset["test"].num_rows == len(pred_vit)


def test_not_fitted_image_class_model(load_dashaidataset: DatasetDict):
    vit = ViTTransformer()

    with pytest.raises(NotFittedError):
        vit.predict(load_dashaidataset)


def test_save_and_load_model(load_dashaidataset: DatasetDict):
    vit = ViTTransformer(num_train_epochs=2, per_device_train_batch_size=32)
    vit.fit(load_dashaidataset)
    vit.save("tests/back/models/vit_model")
    saved_model_vit = ViTTransformer.load("tests/back/models/vit_model")
    assert saved_model_vit.fitted is True
    pred_vit = saved_model_vit.predict(load_dashaidataset)
    assert load_dashaidataset["test"].num_rows == len(pred_vit)
    shutil.rmtree("tests/back/models/vit_model", ignore_errors=True)


def test_get_schema_from_model():
    model_schema = ViTTransformer.get_schema()
    assert type(model_schema) is dict
    assert "type" in model_schema.keys()
    assert model_schema["type"] == "object"
    assert "properties" in model_schema.keys()
    assert type(model_schema["properties"]) is dict
