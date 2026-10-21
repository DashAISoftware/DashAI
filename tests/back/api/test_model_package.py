"""Exporting a run as a package, loading it outside the app, and the endpoint.

Two runs are fitted by hand (training through ModelJob is slow and not what is
under test): a classifier behind a Binarizer preprocessing step, so the fitted
preprocessor has to travel with the package, and a plain regressor.
"""

import io
import json
import os
import subprocess
import sys
import zipfile

import pandas as pd
import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.model_package.export import (
    RunNotExportableError,
    build_package,
)
from DashAI.back.model_package.manifest import (
    MANIFEST_ENTRY,
    PREPROCESSOR_ENTRY,
    SCHEMA_ENTRY,
    ModelPackageError,
)
from tests.back.api.trained_runs import (
    CLASS_COLUMN,
    DERIVED_COLUMN,
    IRIS_CSV,
    RAW_INPUT_COLUMNS,
    REGRESSION_INPUTS,
    SPLITS,
    fit_classifier_behind_preprocessing,
    fit_regressor,
    predicted_in_app,
)


@pytest.fixture(scope="module", name="classifier_run_id")
def fit_a_classifier_behind_preprocessing(
    client: TestClient, dataset_1: Dataset, tmp_path_factory
):
    return fit_classifier_behind_preprocessing(
        client,
        dataset_1,
        tmp_path_factory.mktemp("model-package-classifier"),
        "model-package-classifier-session",
    )


@pytest.fixture(scope="module", name="regressor_run_id")
def fit_a_regressor(client: TestClient, dataset_1: Dataset, tmp_path_factory):
    return fit_regressor(
        client,
        dataset_1,
        tmp_path_factory.mktemp("model-package-regressor"),
        "model-package-regressor-session",
    )


def _export(client, run_id, destination):
    return build_package(
        run_id,
        destination,
        client.app.container["session_factory"],
        client.app.container["component_registry"],
    )


def test_a_package_carries_the_model_preprocessor_and_an_empty_schema(
    client, classifier_run_id, tmp_path
):
    destination = tmp_path / "classifier.dashai-model"
    manifest = _export(client, classifier_run_id, destination)

    assert manifest["kind"] == "model"
    assert manifest["model"]["name"] == "KNeighborsClassifier"
    assert manifest["task"]["name"] == "TabularClassificationTask"
    assert manifest["input_columns"] == [DERIVED_COLUMN]
    assert manifest["output_columns"] == [CLASS_COLUMN]
    assert manifest["has_preprocessing"] is True
    assert manifest["plugins"] == []

    with zipfile.ZipFile(destination) as archive:
        names = set(archive.namelist())
        assert MANIFEST_ENTRY in names
        assert PREPROCESSOR_ENTRY in names
        assert json.loads(archive.read(MANIFEST_ENTRY)) == manifest
        schema_bytes = archive.read(f"{SCHEMA_ENTRY}/data.arrow")

    table = pa.ipc.open_file(pa.py_buffer(schema_bytes)).read_all()
    assert table.num_rows == 0
    types = json.loads(table.schema.metadata[b"dashai_types"])
    assert "Iris-setosa" in types[CLASS_COLUMN]["categories"]


def test_an_unfinished_run_cannot_be_exported(client, dataset_1, tmp_path):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = ModelSession(
            dataset_id=dataset_1.id,
            name="model-package-unfinished-session",
            task_name="TabularClassificationTask",
            input_columns=RAW_INPUT_COLUMNS,
            output_columns=[CLASS_COLUMN],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(SPLITS),
        )
        db.add(session)
        db.commit()
        run = Run(
            model_session_id=session.id,
            model_name="KNeighborsClassifier",
            parameters={},
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={},
            name="Unfinished",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        run_id = run.id

    with pytest.raises(RunNotExportableError):
        _export(client, run_id, tmp_path / "unfinished.dashai-model")


# Runs in a fresh interpreter: inside pytest the ``client`` fixture fills the
# kink container, so only a separate process proves loading never needs it.
LOAD_AND_PREDICT = """
import json, sys
import pandas as pd
from DashAI import load_model

model = load_model(sys.argv[1])
rows = pd.read_csv(sys.argv[2]).head(int(sys.argv[3]))
print(json.dumps(model.predict(rows)))
"""


def _predict_in_fresh_process(package, tmp_path, n_rows):
    env = {**os.environ, "DASHAI_LOCAL_PATH": str(tmp_path / "unused-home")}
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            LOAD_AND_PREDICT,
            str(package),
            str(IRIS_CSV),
            str(n_rows),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize(
    ("run_fixture", "app_columns"),
    [
        ("classifier_run_id", RAW_INPUT_COLUMNS),
        ("regressor_run_id", REGRESSION_INPUTS),
    ],
)
def test_a_loaded_package_predicts_what_the_app_predicts(
    request, client, tmp_path, run_fixture, app_columns
):
    run_id = request.getfixturevalue(run_fixture)
    package = tmp_path / "model.dashai-model"
    _export(client, run_id, package)

    # The CSV read in the fresh process keeps every column, target included,
    # and pandas hands over numpy scalars: both must be accepted as is.
    predicted = _predict_in_fresh_process(package, tmp_path, n_rows=10)

    expected = predicted_in_app(client, run_id, app_columns, n_rows=10)
    if isinstance(expected[0], float):
        assert predicted == pytest.approx(expected)
    else:
        assert predicted == expected


def test_a_file_that_is_not_a_package_is_refused(tmp_path):
    from DashAI import load_model

    not_a_zip = tmp_path / "broken.dashai-model"
    not_a_zip.write_text("not a zip", encoding="utf-8")
    with pytest.raises(ModelPackageError, match="not a DashAI model package"):
        load_model(not_a_zip)

    zip_without_manifest = tmp_path / "empty.dashai-model"
    with zipfile.ZipFile(zip_without_manifest, "w") as archive:
        archive.writestr("something.txt", "hello")
    with pytest.raises(ModelPackageError, match="not a DashAI model package"):
        load_model(zip_without_manifest)


def test_the_endpoint_downloads_the_package(client, regressor_run_id):
    response = client.get(f"/api/v1/run/{regressor_run_id}/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    assert ".dashai-model" in response.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read(MANIFEST_ENTRY))
    assert manifest["model"]["name"] == "LinearRegression"


def test_the_endpoint_answers_404_for_a_missing_run(client):
    response = client.get("/api/v1/run/999999/export")
    assert response.status_code == 404
    # An unknown route also answers 404; the detail tells the two apart.
    assert response.json()["detail"] == "Run not found"


def test_the_endpoint_answers_409_for_an_unfinished_run(client, dataset_1):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = ModelSession(
            dataset_id=dataset_1.id,
            name="model-package-endpoint-unfinished-session",
            task_name="TabularClassificationTask",
            input_columns=RAW_INPUT_COLUMNS,
            output_columns=[CLASS_COLUMN],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(SPLITS),
        )
        db.add(session)
        db.commit()
        run = Run(
            model_session_id=session.id,
            model_name="KNeighborsClassifier",
            parameters={},
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={},
            name="Unfinished endpoint run",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        run_id = run.id

    response = client.get(f"/api/v1/run/{run_id}/export")
    assert response.status_code == 409


def _zip_with_manifest(path, manifest_bytes):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(MANIFEST_ENTRY, manifest_bytes)
    return path


@pytest.mark.parametrize(
    "manifest_bytes",
    [
        json.dumps({"name": "some browser extension"}).encode(),
        json.dumps(["not", "a", "dict"]).encode(),
        b"\xff\xfe not utf-8",
    ],
    ids=["foreign-manifest", "manifest-is-a-list", "manifest-not-utf8"],
)
def test_a_zip_with_a_foreign_manifest_is_refused(tmp_path, manifest_bytes):
    from DashAI import load_model

    package = _zip_with_manifest(tmp_path / "foreign.zip", manifest_bytes)
    with pytest.raises(ModelPackageError, match="not a DashAI model package"):
        load_model(package)


def test_a_folder_or_a_missing_file_is_refused(tmp_path):
    from DashAI import load_model

    with pytest.raises(ModelPackageError, match="not a file"):
        load_model(tmp_path)
    with pytest.raises(ModelPackageError, match="not a file"):
        load_model(tmp_path / "missing.dashai-model")


def test_a_class_that_cannot_be_imported_is_refused(client, regressor_run_id, tmp_path):
    package = tmp_path / "regressor.dashai-model"
    _export(client, regressor_run_id, package)
    broken = tmp_path / "broken-class.dashai-model"
    with zipfile.ZipFile(package) as source, zipfile.ZipFile(broken, "w") as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == MANIFEST_ENTRY:
                manifest = json.loads(data)
                manifest["model"]["module"] = "dashai_plugin_gone.models"
                data = json.dumps(manifest).encode()
            target.writestr(item, data)

    from DashAI import load_model

    with pytest.raises(ModelPackageError, match="dashai_plugin_gone.models"):
        load_model(broken)


def test_missing_input_columns_are_all_named_at_once(
    client, regressor_run_id, tmp_path
):
    package = tmp_path / "regressor.dashai-model"
    _export(client, regressor_run_id, package)
    from DashAI import load_model

    model = load_model(package)
    rows = pd.DataFrame({"SepalLengthCm": [5.1], "Species": ["Iris-setosa"]})

    with pytest.raises(
        ModelPackageError,
        match="Missing input columns: SepalWidthCm, PetalLengthCm",
    ):
        model.predict(rows)


def test_load_model_refuses_a_session_file(tmp_path):
    manifest = {
        "format_version": 1,
        "kind": "session",
        "contents": ["dataset", "session", "runs", "metrics"],
    }
    package = _zip_with_manifest(
        tmp_path / "shared.dashai", json.dumps(manifest).encode()
    )
    from DashAI import load_model

    with pytest.raises(ModelPackageError, match="session"):
        load_model(package)
