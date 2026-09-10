import copy
import json

import pyarrow as pa
import pytest
from datasets import DatasetDict

from DashAI.back.core.artifacts import GroupedArtifacts, PlotlyArtifact
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.explainability.explainers.partial_dependence import PartialDependence
from DashAI.back.explainability.explainers.permutation_feature_importance import (
    PermutationFeatureImportance,
)
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Float

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
OUTPUT_COLUMNS = ["Species"]
TARGETS = [
    "Iris-setosa",
    "Iris-versicolor",
    "Iris-virginica",
]


@pytest.fixture(scope="module", name="dataset")
def tabular_model_fixture():
    dataset_path = "tests/back/explainers/iris.csv"
    dataloader = CSVDataLoader()

    datasetdict = dataloader.load_data(
        filepath_or_buffer=dataset_path,
        temp_path="tests/back/explainers",
        params={
            "separator": ",",
            "schema": {
                "SepalLengthCm": {"type": "Float", "dtype": "float64"},
                "SepalWidthCm": {"type": "Float", "dtype": "float64"},
                "PetalLengthCm": {"type": "Float", "dtype": "float64"},
                "PetalWidthCm": {"type": "Float", "dtype": "float64"},
                "Species": {"type": "Categorical", "dtype": "string"},
            },
        },
    )
    # Since we're not saving to disk, we need to initialize the types manually
    datasetdict.types = datasetdict.types = {
        "SepalLengthCm": Float(arrow_type=pa.float64()),
        "SepalWidthCm": Float(arrow_type=pa.float64()),
        "PetalLengthCm": Float(arrow_type=pa.float64()),
        "PetalWidthCm": Float(arrow_type=pa.float64()),
        "Species": Categorical(
            values=["Iris-setosa", "Iris-versicolor", "Iris-virginica"]
        ),
    }

    new_table = save_types_in_arrow_metadata(
        datasetdict.arrow_table,
        {col: dtype.to_string() for col, dtype in datasetdict.types.items()},
    )

    datasetdict = DashAIDataset(
        new_table, splits=datasetdict.splits, types=datasetdict.types
    )

    total_rows = datasetdict.num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_dataset_dict = split_dataset(
        datasetdict,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    x, y = select_columns(split_dataset_dict, INPUT_COLUMNS, OUTPUT_COLUMNS)

    y = split_dataset(y)
    x = split_dataset(x)

    dataset = x, y

    return dataset


@pytest.fixture(scope="module", name="trained_model")
def trained_model(dataset):
    x, y = dataset
    model = DecisionTreeClassifier(
        criterion="gini",
        max_depth=3,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features=None,
    )
    model.train(x["train"], y["train"])

    return model


def test_partial_dependence(trained_model: BaseModel, dataset):
    parameters = {
        "grid_resolution": 50,
        "lower_percentile": 0.01,
        "upper_percentile": 0.99,
    }
    explainer = PartialDependence(trained_model, **parameters)
    explanation = explainer.explain(
        copy.deepcopy(dataset)
    )  # use deepcopy to avoid modifying the original dataset
    plot = explainer.plot(explanation)

    metadata = explanation.pop("metadata")
    assert set(metadata["target_names"]) == set(TARGETS)

    assert len(explanation) == len(INPUT_COLUMNS)
    # A single grouped artifact with one group (a plotly curve) per feature and
    # class, so the frontend renders a selector instead of an in-figure dropdown.
    assert len(plot) == 1
    grouped = plot[0]
    assert isinstance(grouped, GroupedArtifacts)
    assert len(grouped.groups) == len(INPUT_COLUMNS) * len(TARGETS)
    for group in grouped.groups:
        assert group.title.startswith("Feature: ")
        assert len(group.artifacts) == 1
        artifact = group.artifacts[0]
        assert isinstance(artifact, PlotlyArtifact)
        artifact_dict = artifact.to_dict()
        assert artifact_dict["type"] == "plotly"
        json.loads(artifact_dict["payload"])

    for feature_key in explanation.values():
        assert "grid_values" in feature_key
        assert "average" in feature_key


def test_wrong_parameters_partial_dependence(trained_model: BaseModel):
    parameters = {
        "grid_resolution": 50,
        "lower_percentile": 2,
        "upper_percentile": 1,
    }

    with pytest.raises(
        AssertionError,
    ):
        PartialDependence(trained_model, **parameters)


def test_permutation_feature_importance(trained_model: BaseModel, dataset: DatasetDict):
    parameters = {
        "scoring": "accuracy",
        "n_repeats": 5,
        "random_state": None,
        "max_samples_fraction": 1.0,
    }
    explainer = PermutationFeatureImportance(trained_model, **parameters)
    explanation = explainer.explain(copy.deepcopy(dataset))
    plot = explainer.plot(explanation)

    assert all(
        key in explanation
        for key in ["features", "importances_mean", "importances_std"]
    )
    # A single grouped artifact with one group (a bar chart) per feature count
    # (all features down to one), so the frontend lists the counts in a selector
    # instead of an in-figure dropdown.
    assert len(plot) == 1
    grouped = plot[0]
    assert isinstance(grouped, GroupedArtifacts)
    assert len(grouped.groups) == len(INPUT_COLUMNS)
    for group in grouped.groups:
        assert group.title.startswith("Top ")
        assert len(group.artifacts) == 1
        artifact = group.artifacts[0]
        assert isinstance(artifact, PlotlyArtifact)
        artifact_dict = artifact.to_dict()
        assert artifact_dict["type"] == "plotly"
        json.loads(artifact_dict["payload"])

    for values in explanation.values():
        assert len(values) == len(INPUT_COLUMNS)

    parameters = {
        "scoring": "balanced_accuracy",
        "n_repeats": 5,
        "random_state": None,
        "max_samples_fraction": 1.0,
    }
    explainer = PermutationFeatureImportance(trained_model, **parameters)
    explanation = explainer.explain(copy.deepcopy(dataset))
    plot = explainer.plot(explanation)

    assert all(
        key in explanation
        for key in ["features", "importances_mean", "importances_std"]
    )
    assert len(plot) == 1
    assert len(plot[0].groups) == len(INPUT_COLUMNS)

    for values in explanation.values():
        assert len(values) == len(INPUT_COLUMNS)


def plot(self, explanation: list[dict]):
    """Create explanation plots using plotly, tolerant to missing metadata."""
    import numpy as np
    import pandas as pd

    exp = explanation.copy()

    max_features = 8
    metadata = exp.pop("metadata", {}) or {}
    base_values = exp.pop("base_values", None)

    # --- Feature names (fallbacks si no vienen en metadata)
    feature_names = metadata.get("feature_names", None)
    if feature_names is None:
        feature_names = getattr(self, "feature_names_", None)
    # lo terminamos de resolver por instancia si aún es None

    # --- Target names (fallbacks si no vienen en metadata)
    global_target_names = metadata.get("target_names", None)
    if global_target_names is None:
        global_target_names = getattr(self, "target_names_", None)
    # si sigue None, deducimos por instancia con len(model_prediction)

    plots = []

    # Iterar por las instancias de la explicación
    for _, ex_i in exp.items():
        instance_values = ex_i["instance_values"]
        model_prediction = ex_i["model_prediction"]

        # target_names por instancia si no hay globales
        if global_target_names is None:
            target_names = [str(k) for k in range(len(model_prediction))]
        else:
            target_names = global_target_names

        y_pred_class = int(np.argmax(model_prediction))
        y_pred_name = target_names[y_pred_class]
        y_pred_pbb = float(np.round(model_prediction[y_pred_class], 2))

        # feature_names por instancia si aún no estaban
        feats = feature_names
        if feats is None:
            feats = [f"feature_{k}" for k in range(len(instance_values))]
        feats = np.asarray(feats, dtype=str).reshape(-1)

        # --- Normaliza SHAP values (lista por clase, 2D, Explanation, etc.)
        sv = ex_i["shap_values"]

        # 1) Si es lista (típico multiclass: una entrada por clase)
        if isinstance(sv, list):
            try:
                sv_raw = np.asarray(sv[y_pred_class])
            except Exception:
                sv_raw = np.asarray(sv)
        else:
            sv_raw = np.asarray(sv)

        # 2) If shap.Explanation
        try:
            from shap._explanation import Explanation

            if isinstance(sv, Explanation):
                sv_raw = np.asarray(sv.values)
        except Exception:
            pass

        # 3) Resolver formas 2D con eje de clases/características
        if sv_raw.ndim == 2:
            if sv_raw.shape[0] == feats.size and sv_raw.shape[1] != feats.size:
                # n_features, n_classes
                sv_raw = sv_raw[:, y_pred_class]
            elif sv_raw.shape[1] == feats.size and sv_raw.shape[0] != feats.size:
                # n_classes, n_features
                sv_raw = sv_raw[y_pred_class, :]
            elif (
                sv_raw.shape[0] == 1
                and sv_raw.shape[1] == feats.size
                or sv_raw.shape[1] == 1
                and sv_raw.shape[0] == feats.size
            ):
                sv_raw = sv_raw.reshape(-1)
            else:
                raise ValueError(f"shap_values {sv_raw.shape} n_features={feats.size}")
        else:
            sv_raw = sv_raw.reshape(-1)

        # --- Asegura mismas longitudes (recorte defensivo si algo llegó desalineado)
        vals = np.asarray(instance_values).reshape(-1)
        n = min(vals.size, feats.size, sv_raw.size)
        if not (vals.size == feats.size == sv_raw.size):
            print(
                f"[WARN] Desalineado: len(values)={vals.size}, "
                f"len(features)={feats.size}, len(shap_values)={sv_raw.size}. "
                f"Se recorta a {n}."
            )
            vals = vals[:n]
            feats = feats[:n]
            sv_raw = sv_raw[:n]

        # --- Construcción del DataFrame
        data = pd.DataFrame(
            {
                "values": vals,
                "shap_values": sv_raw,
                "features": feats,
            }
        )

        # --- Resto del pipeline
        data["shap_values_abs"] = np.abs(data["shap_values"])
        data = data.sort_values(by="shap_values_abs", ascending=True)

        if len(data) > max_features:
            data_1 = data.iloc[-max_features:, :]
            data_2 = data.iloc[:-max_features, :]
            others = pd.DataFrame.from_dict(
                {
                    "values": [None],
                    "shap_values": [float(np.round(data_2["shap_values"].sum(), 3))],
                    "shap_values_abs": [None],
                    "features": ["Others"],
                }
            )
            data = pd.concat([others, data_1], ignore_index=True)

        data["label"] = data["features"] + "=" + data["values"].map(str)

        # --- base_value por clase (tolera escalar o vector)
        base_arr = np.asarray(base_values) if base_values is not None else np.array(0.0)
        if base_arr.ndim == 0:
            base_value = float(base_arr)
        else:
            # si no hay suficientes clases, caemos a 0.0
            base_value = (
                float(base_arr[y_pred_class]) if y_pred_class < base_arr.size else 0.0
            )

        plot = self._create_plot(data, base_value, y_pred_pbb, y_pred_name)
        plots.append(plot)

    return plots
