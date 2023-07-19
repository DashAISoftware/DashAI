import io
import shutil

import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.tasks.translation_task import TranslationTask


@pytest.fixture(scope="session", name="load_dashaidataset")
def fixture_load_dashaidataset():
    test_dataset_path = "tests/back/models/translationEngSpaDatasetSmall.json"
    dataloader_test = JSONDataLoader()
    params = {"data_key": "data"}
    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    datasetdict = dataloader_test.load_data("tests/back/models", params, file=file)
    inputs_columns = ["text"]
    outputs_columns = ["class"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    translation_task = TranslationTask()
    datasetdict = translation_task.prepare_for_task(datasetdict)
    translation_task.validate_dataset_for_task(datasetdict, "EngSpaDataset")
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, seed=42
    )
    return separate_datasetdict


@pytest.fixture(scope="session", name="model_fit")
def translation_model_fit(load_dashaidataset: DatasetDict):
    params = {"num_train_epochs": 1, "batch_size": 32, "device": "cpu"}
    opus_mt_en_es = OpusMtEnESTransformer(**params)
    opus_mt_en_es.fit(load_dashaidataset["train"])
    return opus_mt_en_es


def test_fitted_translation_model(model_fit: OpusMtEnESTransformer):
    assert model_fit.fitted is True


def test_predict_translation_model(
    model_fit: OpusMtEnESTransformer, load_dashaidataset: DatasetDict
):
    pred_opus_mt_en_es = model_fit.predict(load_dashaidataset["test"])
    assert load_dashaidataset["test"].num_rows == len(pred_opus_mt_en_es)


def test_not_fitted_translation_model(load_dashaidataset: DatasetDict):
    params = {"num_train_epochs": 1, "batch_size": 32, "device": "cpu"}
    opus_mt_en_es = OpusMtEnESTransformer(**params)

    with pytest.raises(NotFittedError):
        opus_mt_en_es.predict(load_dashaidataset["test"])


def test_save_and_load_model(
    model_fit: OpusMtEnESTransformer, load_dashaidataset: DatasetDict
):
    model_fit.save("tests/back/models/opus_mt_en_es_model")
    saved_model_opus_mt_en_es = OpusMtEnESTransformer.load(
        "tests/back/models/opus_mt_en_es_model"
    )
    assert saved_model_opus_mt_en_es.fitted is True
    pred_opus_mt_en_es = saved_model_opus_mt_en_es.predict(load_dashaidataset["test"])
    assert load_dashaidataset["test"].num_rows == len(pred_opus_mt_en_es)
    shutil.rmtree("tests/back/models/opus_mt_en_es_model", ignore_errors=True)


def test_get_schema_from_model():
    model_schema = OpusMtEnESTransformer.get_schema()
    assert type(model_schema) is dict
    assert "type" in model_schema
    assert model_schema["type"] == "object"
    assert "properties" in model_schema
    assert type(model_schema["properties"]) is dict
