"""Translation Metrics Tests."""
import io
from typing import Tuple

import numpy as np
import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dashai_dataset import select_columns
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.metrics.translation.bleu import Bleu
from DashAI.back.metrics.translation.ter import Ter
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.tasks.translation_task import TranslationTask


@pytest.fixture(scope="module", name="dataset")
def dataset_fixture():
    test_dataset_path = "tests/back/metrics/translationEngSpaDatasetSmall.json"
    json_dataloader = JSONDataLoader()

    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    dataset_dict = json_dataloader.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/models",
        params={"data_key": "data"},
    )

    dashai_dataset = to_dashai_dataset(dataset_dict)

    inputs_columns = ["text"]
    outputs_columns = ["class"]

    translation_task = TranslationTask()
    dashai_dataset = translation_task.prepare_for_task(dashai_dataset, outputs_columns)
    translation_task.validate_dataset_for_task(
        dashai_dataset, "EngSpaDataset", inputs_columns, outputs_columns
    )

    split_dataset = json_dataloader.split_dataset(
        dashai_dataset, 0.7, 0.1, 0.2, seed=42
    )

    divided_dataset = select_columns(split_dataset, inputs_columns, outputs_columns)

    return divided_dataset


@pytest.fixture(scope="module", name="translation_pred")
def fixture_translation_pred(dataset: Tuple[DatasetDict, DatasetDict]):
    params = {"num_train_epochs": 1, "batch_size": 32, "device": "cpu"}
    model = OpusMtEnESTransformer(**params)
    model.fit(dataset[0]["train"], dataset[1]["train"])
    return model.predict(dataset[1]["test"])


def test_bleu(dataset: Tuple[DatasetDict, DatasetDict], translation_pred: np.ndarray):
    score = Bleu.score(dataset[1]["test"], translation_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_ter(dataset: Tuple[DatasetDict, DatasetDict], translation_pred: np.ndarray):
    score = Ter.score(dataset[1]["test"], translation_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_metrics_different_input_sizes(dataset: Tuple[DatasetDict, DatasetDict]):
    pred_opus_mt_en_es = dataset[1]["test"]["class"]
    with pytest.raises(
        ValueError, match="The length of the true and predicted labels must be equal."
    ):
        Bleu.score(dataset[1]["validation"], pred_opus_mt_en_es)

    with pytest.raises(
        ValueError, match="The length of the true and predicted labels must be equal."
    ):
        Ter.score(dataset[1]["validation"], pred_opus_mt_en_es)
