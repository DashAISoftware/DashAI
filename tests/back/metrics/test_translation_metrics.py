import io

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.metrics.translation.bleu import Bleu
from DashAI.back.metrics.translation.ter import Ter
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
    translation_task = TranslationTask.create()
    datasetdict = translation_task.prepare_for_task(datasetdict)
    translation_task.validate_dataset_for_task(datasetdict, "EngSpaDataset")
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, seed=42
    )
    return separate_datasetdict


@pytest.fixture(scope="session", name="opus_mt_en_es")
def translation_model_fit(load_dashaidataset: DatasetDict):
    opus_mt_en_es = OpusMtEnESTransformer(
        num_train_epochs=1, per_device_train_batch_size=32
    )
    opus_mt_en_es.fit(load_dashaidataset["train"])
    return opus_mt_en_es


def test_bleu(load_dashaidataset: DatasetDict, opus_mt_en_es: OpusMtEnESTransformer):
    pred_opus_mt_en_es = opus_mt_en_es.predict(load_dashaidataset["test"])
    bleu = Bleu.score(load_dashaidataset["test"], pred_opus_mt_en_es)
    try:
        isinstance(
            bleu,
            float,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_accuracy: {repr(e)}")


def test_ter(load_dashaidataset: DatasetDict, opus_mt_en_es: OpusMtEnESTransformer):
    pred_opus_mt_en_es = opus_mt_en_es.predict(load_dashaidataset["test"])
    ter = Ter.score(load_dashaidataset["test"], pred_opus_mt_en_es)
    try:
        isinstance(
            ter,
            float,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_accuracy: {repr(e)}")


def test_wrong_size_metric(
    load_dashaidataset: DatasetDict, opus_mt_en_es: OpusMtEnESTransformer
):
    pred_opus_mt_en_es = opus_mt_en_es.predict(load_dashaidataset["validation"])
    with pytest.raises(
        ValueError, match="The length of the true and predicted labels must be equal."
    ):
        Bleu.score(load_dashaidataset["test"], pred_opus_mt_en_es)
