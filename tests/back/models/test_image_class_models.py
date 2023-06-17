import shutil

import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.models.hugging_face.vit_transformer import ViTTransformer
from DashAI.back.tasks.image_classification_task import ImageClassificationTask


@pytest.fixture(scope="session", name="load_dashaidataset")
def fixture_load_dashaidataset():
    test_dataset_path = "tests/back/models/beans_dataset_small.zip"
    dataloader_test = ImageDataLoader()
    header = Headers({"Content-Type": "application/zip"})
    file = open(test_dataset_path, "rb")  # noqa: SIM115
    upload_file = UploadFile(filename=test_dataset_path, file=file, headers=header)
    datasetdict = dataloader_test.load_data(
        "tests/back/dataloaders/beans_dataset", file=upload_file
    )
    file.close()
    inputs_columns = ["image"]
    outputs_columns = ["label"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    image_task = ImageClassificationTask.create()
    separate_datasetdict = image_task.prepare_for_task(separate_datasetdict)
    image_task.validate_dataset_for_task(separate_datasetdict, "beans_dataset")

    yield datasetdict
    shutil.rmtree("tests/back/tasks/beans_dataset", ignore_errors=True)


@pytest.fixture(scope="session", name="model_fit")
def image_class_model_fit(load_dashaidataset: DatasetDict):
    vit = ViTTransformer()
    vit.fit(load_dashaidataset["train"])
    return vit


@pytest.fixture(scope="session", name="model_fit_with_params")
def image_class_model_fit_with_params(load_dashaidataset: DatasetDict):
    vit = ViTTransformer(num_train_epochs=1, per_device_train_batch_size=32)
    vit.fit(load_dashaidataset["train"])
    return vit


def test_fitted_image_class_model(model_fit: ViTTransformer):
    assert model_fit.fitted is True


def test_fitted_image_class_model_with_params(
    model_fit_with_params: ViTTransformer,
):
    assert model_fit_with_params.fitted is True


def test_predict_image_class_model(
    model_fit: ViTTransformer, load_dashaidataset: DatasetDict
):
    pred_vit = model_fit.predict(load_dashaidataset["test"])
    assert load_dashaidataset["test"].num_rows == len(pred_vit)


def test_not_fitted_image_class_model(load_dashaidataset: DatasetDict):
    vit = ViTTransformer()

    with pytest.raises(NotFittedError):
        vit.predict(load_dashaidataset["test"])


def test_save_and_load_model(
    model_fit: ViTTransformer, load_dashaidataset: DatasetDict
):
    model_fit.save("tests/back/models/vit_model")
    saved_model_vit = ViTTransformer.load("tests/back/models/vit_model")
    assert saved_model_vit.fitted is True
    pred_vit = saved_model_vit.predict(load_dashaidataset["test"])
    assert load_dashaidataset["test"].num_rows == len(pred_vit)
    shutil.rmtree("tests/back/models/vit_model", ignore_errors=True)


def test_get_schema_from_model():
    model_schema = ViTTransformer.get_schema()
    assert type(model_schema) is dict
    assert "type" in model_schema
    assert model_schema["type"] == "object"
    assert "properties" in model_schema
    assert type(model_schema["properties"]) is dict
