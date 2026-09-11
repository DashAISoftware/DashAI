import os
from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest
from datasets import DatasetDict

from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    to_dashai_dataset,
)
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
from DashAI.back.models.model_factory import ModelFactory
from DashAI.back.models.scikit_learn.bow_text_classification_model import (
    BagOfWordsTextClassificationModel,
)
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Text
from tests.back.scratch import scratch_dir


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    """Setup a test registry with test task, dataloader and model components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            JSONDataLoader,
            ModelJob,
            OptunaOptimizer,
            RandomForestClassifier,
            BagOfWordsTextClassificationModel,
        ]
    )

    monkeypatch.setitem(
        container._services,
        "component_registry",
        test_registry,
    )
    return test_registry


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
    datasetdict.types = datasetdict.types = {
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

    return (x, y)


@pytest.fixture(scope="module", name="model_params")
def model_params_fixture() -> dict:
    return {
        "tabular_classifier": {
            "component": "RandomForestClassifier",
            "params": {
                "n_estimators": 1,
                "max_depth": None,
                "min_samples_split": 2,
                "min_samples_leaf": 1,
                "max_leaf_nodes": None,
                "random_state": None,
            },
        },
        "ngram_min_n": 1,
        "ngram_max_n": 1,
    }


@pytest.fixture(name="sample_model")
def model_fixture(model_params: dict):
    bowtc_model = BagOfWordsTextClassificationModel
    factory = ModelFactory(bowtc_model, model_params)
    return factory.model


def test_model_initialization(sample_model: BagOfWordsTextClassificationModel):
    assert sample_model.classifier is not None
    assert sample_model.vectorizer is not None
    assert isinstance(sample_model, BagOfWordsTextClassificationModel)
    assert isinstance(sample_model.classifier, RandomForestClassifier)
    assert sample_model.vectorizer.ngram_range == (1, 1)


def test_vectorize_text(
    splited_dataset: DatasetDict, sample_model: BagOfWordsTextClassificationModel
):
    x, y = splited_dataset
    x = x["train"]
    input_column = x.column_names[0]
    sample_model.vectorizer.fit(x[input_column])
    vectorizer_func = sample_model.get_vectorizer(input_column)
    vectorized_dataset = x.map(vectorizer_func, remove_columns="text")
    assert len(vectorized_dataset) > 0
    assert "text0" in vectorized_dataset.column_names


def test_fit_model(
    splited_dataset: DatasetDict, sample_model: BagOfWordsTextClassificationModel
):
    x, y = splited_dataset
    x = x["train"]
    y = y["train"]
    sample_model.train(x, y)

    assert hasattr(sample_model.vectorizer, "vocabulary_")
    assert hasattr(sample_model.classifier, "estimators_")


def test_predict_model(
    splited_dataset: DatasetDict, sample_model: BagOfWordsTextClassificationModel
):
    x, y = splited_dataset
    x = x["test"]
    input_column = x.column_names[0]
    sample_model.vectorizer.fit(x[input_column])
    vectorizer_func = sample_model.get_vectorizer(input_column)
    vectorized_dataset = x.map(vectorizer_func, remove_columns="text")
    vectorized_dataset = to_dashai_dataset(vectorized_dataset)
    sample_model.classifier.train(vectorized_dataset, y["test"])
    predictions = sample_model.predict(x)
    assert isinstance(predictions, np.ndarray)
    assert len(predictions) == len(y["test"])


def test_save_and_load_model(
    splited_dataset: DatasetDict,
    sample_model: BagOfWordsTextClassificationModel,
    tmp_path: Path,
):
    x, y = splited_dataset
    sample_model.train(x["train"], y["train"])
    nwft_filename = os.path.join(tmp_path, "nwft_model")
    sample_model.save(nwft_filename)
    loaded_model = sample_model.load(nwft_filename)

    original_predictions = sample_model.predict(x["test"])
    loaded_predictions = loaded_model.predict(x["test"])

    assert np.array_equal(original_predictions, loaded_predictions)

    os.remove(nwft_filename)


def test_get_schema_from_model_class():
    model_schema = BagOfWordsTextClassificationModel.get_schema()

    assert isinstance(model_schema, dict)
    assert "type" in model_schema
    assert model_schema["type"] == "object"
    assert "properties" in model_schema
    assert isinstance(model_schema["properties"], dict)
    assert {"tabular_classifier", "ngram_min_n", "ngram_max_n"} == model_schema[
        "properties"
    ].keys()
    assert model_schema["properties"]["tabular_classifier"]["type"] == "object"
    assert (
        model_schema["properties"]["tabular_classifier"]["parent"]
        == "TabularClassificationModel"
    )
    assert model_schema["properties"]["ngram_min_n"]["type"] == "integer"
    assert model_schema["properties"]["ngram_min_n"]["minimum"] == 1
    assert model_schema["properties"]["ngram_min_n"]["placeholder"] == 1
    assert model_schema["properties"]["ngram_max_n"]["type"] == "integer"
    assert model_schema["properties"]["ngram_max_n"]["minimum"] == 1
    assert model_schema["properties"]["ngram_max_n"]["placeholder"] == 1
    assert "required" in model_schema
    assert set(model_schema["required"]) == {
        "tabular_classifier",
        "ngram_min_n",
        "ngram_max_n",
    }
