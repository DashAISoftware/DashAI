import io
import os

import numpy as np
import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.core.schema_fields.utils import fill_objects
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.models.scikit_learn.bow_text_classification_model import (
    BagOfWordsTextClassificationModel,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel


@pytest.fixture(scope="module", name="split_dataset")
def splited_dataset_fixture():
    test_dataset_path = "tests/back/models/dummy_text.json"
    dataloader_test = JSONDataLoader()

    with open(test_dataset_path, "r") as file:
        json_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(json_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/models",
        params={"data_key": "data"},
    )

    datasetdict = to_dashai_dataset(
        datasetdict,
        inputs_columns=[
            "text",
        ],
        outputs_columns=["class"],
    )

    split_dataset = dataloader_test.split_dataset(
        datasetdict,
        train_size=0.6,
        test_size=0.2,
        val_size=0.2,
        class_column=datasetdict["train"].outputs_columns[0],
    )

    return split_dataset


@pytest.fixture(scope="module", name="model_params")
def model_params_fixture() -> dict:
    raw_params = {
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
    validate_params = BagOfWordsTextClassificationModel.SCHEMA.model_validate(
        raw_params
    )
    return fill_objects(validate_params)


def test_predict_tabular_models(split_dataset: DatasetDict, model_params: dict):
    bowtc_model = BagOfWordsTextClassificationModel(**model_params)
    bowtc_model.fit(split_dataset["train"])

    y_pred_bowtcm = bowtc_model.predict(split_dataset["test"])

    assert isinstance(y_pred_bowtcm, np.ndarray)

    assert split_dataset["test"].num_rows == len(y_pred_bowtcm)


def test_save_and_load_model(split_dataset: DatasetDict, model_params: dict):
    bowtc_model = BagOfWordsTextClassificationModel(**model_params)
    bowtc_model.fit(split_dataset["train"])

    nwft_filename = "tests/back/models/nwft_model"
    bowtc_model.save(nwft_filename)
    loaded_model = SklearnLikeModel.load(nwft_filename)

    y_pred_bowtcm = loaded_model.predict(split_dataset["test"])

    assert isinstance(y_pred_bowtcm, np.ndarray)
    assert split_dataset["test"].num_rows == len(y_pred_bowtcm)

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
