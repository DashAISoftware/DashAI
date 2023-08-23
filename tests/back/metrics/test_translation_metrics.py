"""Translation Metrics Tests."""
import io

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.metrics.translation.bleu import Bleu
from DashAI.back.metrics.translation.ter import Ter
from DashAI.back.tasks.translation_task import TranslationTask


@pytest.fixture(scope="module", name="test_dataset")
def translation_metrics_tests_fixture():
    test_dataset_path = "tests/back/metrics/translationEngSpaDatasetSmall.json"
    test_dataloader = JSONDataLoader()

    with open(test_dataset_path, "r", encoding="utf8") as file:
        json_data = file.read()
        json_binary = io.BytesIO(bytes(json_data, encoding="utf8"))
        file = UploadFile(json_binary)

    dataset_dict = test_dataloader.load_data(
        file=file,
        temp_path="tests/back/models",
        params={"data_key": "data"},
    )

    dashai_dataset = to_dashai_dataset(
        dataset_dict,
        inputs_columns=["text"],
        outputs_columns=["class"],
    )

    translation_task = TranslationTask()
    dashai_dataset = translation_task.prepare_for_task(dashai_dataset)
    translation_task.validate_dataset_for_task(dashai_dataset, "EngSpaDataset")

    split_dataset = test_dataloader.split_dataset(
        dashai_dataset, 0.7, 0.1, 0.2, seed=42
    )
    return split_dataset


def test_bleu(test_dataset: DatasetDict):
    pred_opus_mt_en_es = test_dataset["test"]["class"]
    score = Bleu.score(test_dataset["test"], pred_opus_mt_en_es)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_ter(test_dataset: DatasetDict):
    pred_opus_mt_en_es = test_dataset["test"]["class"]
    score = Ter.score(test_dataset["test"], pred_opus_mt_en_es)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_metrics_different_input_sizes(test_dataset: DatasetDict):
    pred_opus_mt_en_es = test_dataset["test"]["class"]
    with pytest.raises(
        ValueError, match="The length of the true and predicted labels must be equal."
    ):
        Bleu.score(test_dataset["validation"], pred_opus_mt_en_es)

    with pytest.raises(
        ValueError, match="The length of the true and predicted labels must be equal."
    ):
        Ter.score(test_dataset["validation"], pred_opus_mt_en_es)
