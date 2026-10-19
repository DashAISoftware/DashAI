# flake8: noqa: ERA001
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    to_dashai_dataset,
)
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.models.hugging_face.deberta_v3_transformer import DebertaV3Transformer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Text
from tests.back.scratch import scratch_dir


@pytest.fixture(scope="module", name="splited_dataset")
def splited_dataset_fixture():
    test_dataset_path = "tests/back/models/dummy_text.json"
    dataloader_test = JSONDataLoader()

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path=scratch_dir("models"),
        params={
            "data_key": "data",
            "schema": {
                "text": {"type": "Text", "dtype": "string"},
                "class": {"type": "Categorical", "dtype": "string"},
            },
        },
    )

    datasetdict = to_dashai_dataset(datasetdict)

    datasetdict.types = {
        "text": Text(arrow_type=pa.string()),
        "class": Categorical(values=["0", "1"]),
    }

    new_table = save_types_in_arrow_metadata(
        datasetdict.arrow_table,
        {col: dtype.to_string() for col, dtype in datasetdict.types.items()},
    )

    datasetdict = DashAIDataset(
        new_table, splits=datasetdict.splits, types=datasetdict.types
    )

    splited_dataset = split_dataset(
        datasetdict,
        train_indexes=[0, 1, 2],
        test_indexes=[3, 4],
        val_indexes=[5, 6],
    )

    x, y = select_columns(
        splited_dataset,
        ["text"],
        ["class"],
    )
    x = split_dataset(x)
    y = split_dataset(y)
    y["train"] = y["train"].map(lambda example: {"class": int(example["class"])})
    y["test"] = y["test"].map(lambda example: {"class": int(example["class"])})
    y["validation"] = y["validation"].map(
        lambda example: {"class": int(example["class"])}
    )

    return (x, y)


@pytest.fixture
def sample_model():
    model = DebertaV3Transformer(
        num_train_epochs=2,
        batch_size=16,
        learning_rate=5e-5,
        device="CPU",
        weight_decay=0.01,
        log_train_every_n_epochs=None,
        log_train_every_n_steps=None,
        log_validation_every_n_epochs=None,
        log_validation_every_n_steps=None,
    )
    return model


def test_model_initialization(sample_model):
    assert sample_model.model is not None
    assert sample_model.tokenizer is not None
    assert sample_model.model_name == "microsoft/deberta-v3-base"
    assert sample_model.fitted is False


def test_tokenize_data(sample_model, splited_dataset):
    x, y = splited_dataset
    x = x["train"]
    tokenized_dataset = sample_model.tokenize_data(x)

    assert "input_ids" in tokenized_dataset.features
    assert "attention_mask" in tokenized_dataset.features
    assert len(tokenized_dataset) == len(x)
