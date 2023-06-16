import io

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.metrics.translation.bleu import Bleu
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.tasks.translation_task import TranslationTask


@pytest.fixture(scope="module", name="load_dashaidataset")
def fixture_load_dashaidataset():
    test_dataset_path = "tests/back/tasks/translationEngSpaDatasetSmall.json"
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
    text_task = TranslationTask.create()
    datasetdict = text_task.prepare_for_task(datasetdict)
    text_task.validate_dataset_for_task(datasetdict, "IMDBDataset")
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )
    yield separate_datasetdict


def test_bleu(load_dashaidataset: DatasetDict):
    opus_mt_en_es = OpusMtEnESTransformer()
    opus_mt_en_es.fit(load_dashaidataset)
    pred_distilbert = opus_mt_en_es.predict(load_dashaidataset)
    bleu = Bleu.score(load_dashaidataset["test"], pred_distilbert)
    try:
        isinstance(
            bleu,
            float,
        )
    except Exception as e:
        pytest.fail(f"Unexpected error in test_accuracy: {repr(e)}")
