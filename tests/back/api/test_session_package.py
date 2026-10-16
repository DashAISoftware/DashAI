"""Exporting a model session as a .dashai file and importing it back."""

import hashlib
import json
import tempfile
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import Dataset, Metric, ModelSession, Run
from DashAI.back.model_package.manifest import (
    MissingPluginError,
    ModelPackageError,
    UnsupportedPackageFormatError,
    WrongPackageKindError,
)
from DashAI.back.session_package import load as session_load
from DashAI.back.session_package.export import (
    RUN_FIELDS,
    SESSION_FIELDS,
    SessionNotExportableError,
    SessionNotFoundError,
    build_session_package,
    export_preview,
)
from DashAI.back.session_package.load import (
    UnsafePackageError,
    import_session_package,
    unique_name,
)
from tests.back.api.trained_runs import (
    RAW_INPUT_COLUMNS,
    REGRESSION_INPUTS,
    add_metrics,
    fit_classifier_behind_preprocessing,
    fit_regressor,
    new_run,
    predicted_in_app,
)


def _session_of(client, run_id):
    with client.app.container["session_factory"]() as db:
        return db.get(Run, run_id).model_session_id


@pytest.fixture(scope="module", name="classifier")
def a_classifier_session_with_runs_in_every_state(
    client: TestClient, dataset_1: Dataset, tmp_path_factory
):
    """A trained run, a never trained one, one in progress and one whose
    model file is gone, all in the session with preprocessing."""
    session_factory = client.app.container["session_factory"]
    trained = fit_classifier_behind_preprocessing(
        client,
        dataset_1,
        tmp_path_factory.mktemp("session-package-classifier"),
        "session-package-classifier-session",
    )
    add_metrics(session_factory, trained)
    session_id = _session_of(client, trained)

    never_trained = new_run(session_factory, session_id, "KNeighborsClassifier", {})
    in_progress = new_run(session_factory, session_id, "KNeighborsClassifier", {})
    with session_factory() as db:
        db.get(Run, in_progress).set_status_as_delivered()
        db.commit()
    gone = tmp_path_factory.mktemp("session-package-gone") / "model"
    gone.write_bytes(b"model")
    lost_model = new_run(session_factory, session_id, "KNeighborsClassifier", {}, gone)
    gone.unlink()

    return {
        "session_id": session_id,
        "trained": trained,
        "never_trained": never_trained,
        "in_progress": in_progress,
        "lost_model": lost_model,
    }


@pytest.fixture(scope="module", name="regressor")
def a_regression_session(client: TestClient, dataset_1: Dataset, tmp_path_factory):
    trained = fit_regressor(
        client,
        dataset_1,
        tmp_path_factory.mktemp("session-package-regressor"),
        "session-package-regressor-session",
    )
    return {"session_id": _session_of(client, trained), "trained": trained}


def _build(client, session_id, run_ids, destination, include_trained_models=True):
    return build_session_package(
        session_id,
        run_ids,
        include_trained_models,
        destination,
        client.app.container["session_factory"],
        client.app.container["component_registry"],
    )


def _read(package):
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        recipe = json.loads(archive.read("session.json"))
        arrow = archive.read("dataset/data.arrow")
    return names, manifest, recipe, arrow


def test_a_session_package_carries_dataset_recipe_models_and_metrics(
    client, classifier, tmp_path
):
    package = tmp_path / "classifier.dashai"
    _build(
        client,
        classifier["session_id"],
        [classifier["trained"], classifier["never_trained"]],
        package,
    )

    names, manifest, recipe, arrow = _read(package)
    assert manifest["kind"] == "session"
    assert manifest["format_version"] == 1
    assert manifest["includes_trained_models"] is True
    assert manifest["contents"] == ["dataset", "session", "runs", "metrics"]
    assert manifest["dataset_hash"] == hashlib.sha256(arrow).hexdigest()
    assert {"dataset/data.arrow", "dataset/splits.json"} <= names
    assert "preprocessing/final.pkl" in names
    assert "runs/0/model" in names

    assert recipe["session"]["name"] == "session-package-classifier-session"
    assert recipe["session"]["preprocessing"]["steps"][0]["converter"] == "Binarizer"
    assert recipe["dataset"]["name"] == "test_csv_1"
    trained, never_trained = recipe["runs"]
    assert trained["status"] == "FINISHED"
    assert trained["model_entry"] == "runs/0/model"
    assert {(m["split"], m["level"]) for m in trained["metrics"]} == {
        ("TRAIN", "LAST"),
        ("VALIDATION", "LAST"),
        ("TEST", "LAST"),
        ("VALIDATION", "TRIAL"),
    }
    assert never_trained["status"] == "NOT_STARTED"
    assert never_trained["model_entry"] is None
    assert never_trained["metrics"] == []
    assert not any(name.startswith("runs/1/") for name in names)


def test_only_the_chosen_runs_are_exported(client, classifier, tmp_path):
    package = tmp_path / "one-run.dashai"
    _build(client, classifier["session_id"], [classifier["never_trained"]], package)

    _, manifest, recipe, _ = _read(package)
    assert len(recipe["runs"]) == 1
    assert manifest["info"]["run_count"] == 1


def test_recipe_only_leaves_out_models_and_preprocessing(client, classifier, tmp_path):
    package = tmp_path / "recipe.dashai"
    _build(
        client,
        classifier["session_id"],
        [classifier["trained"]],
        package,
        include_trained_models=False,
    )

    names, manifest, recipe, _ = _read(package)
    assert manifest["includes_trained_models"] is False
    assert not any(name.startswith(("runs/", "preprocessing/")) for name in names)
    assert recipe["runs"][0]["status"] == "NOT_STARTED"
    assert recipe["runs"][0]["metrics"] == []


def test_a_finished_run_without_its_model_file_goes_as_a_recipe(
    client, classifier, tmp_path
):
    package = tmp_path / "lost.dashai"
    _build(client, classifier["session_id"], [classifier["lost_model"]], package)

    names, _, recipe, _ = _read(package)
    assert recipe["runs"][0]["status"] == "NOT_STARTED"
    assert not any(name.startswith("runs/") for name in names)

    preview = export_preview(
        classifier["session_id"], client.app.container["session_factory"]
    )
    lost = next(r for r in preview["runs"] if r["id"] == classifier["lost_model"])
    assert lost["missing_model_file"] is True
    assert lost["with_model"] is False


@pytest.mark.parametrize("which", ["none", "in_progress", "foreign"])
def test_export_refuses_no_runs_runs_in_progress_and_foreign_runs(
    client, classifier, regressor, tmp_path, which
):
    run_ids = {
        "none": [],
        "in_progress": [classifier["in_progress"]],
        "foreign": [regressor["trained"]],
    }[which]
    with pytest.raises(SessionNotExportableError):
        _build(client, classifier["session_id"], run_ids, tmp_path / "x.dashai")


def test_a_missing_session_cannot_be_exported(client, tmp_path):
    with pytest.raises(SessionNotFoundError):
        _build(client, 999999, [1], tmp_path / "x.dashai")


def test_the_preview_lists_runs_and_sizes(client, classifier):
    preview = export_preview(
        classifier["session_id"], client.app.container["session_factory"]
    )

    assert preview["session_name"] == "session-package-classifier-session"
    assert preview["dataset_name"] == "test_csv_1"
    runs = {run["id"]: run for run in preview["runs"]}
    trained = runs[classifier["trained"]]
    assert trained["with_model"] is True
    assert trained["goal_metric_value"] == pytest.approx(0.93)
    assert trained["status"] == RunStatus.FINISHED.name
    assert runs[classifier["in_progress"]]["in_progress"] is True
    assert runs[classifier["never_trained"]]["with_model"] is False
    sizes = preview["size_bytes"]
    assert sizes["with_models"] > sizes["recipe_only"] > 0


# Importing ------------------------------------------------------------------


def _import(client, package):
    container = client.app.container
    return import_session_package(
        package,
        container["session_factory"],
        container["component_registry"],
        container["config"],
        container["job_queue"],
    )


def _export_all(client, case, destination, include_trained_models=True):
    _build(
        client,
        case["session_id"],
        [case["trained"]],
        destination,
        include_trained_models,
    )
    return destination


def _rewrite(package, destination, manifest=None, recipe=None, extra=None):
    """Copy a package changing its manifest or recipe, or adding entries."""
    with zipfile.ZipFile(package) as source, zipfile.ZipFile(destination, "w") as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "manifest.json" and manifest:
                data = json.dumps(manifest(json.loads(data))).encode()
            if item.filename == "session.json" and recipe:
                data = json.dumps(recipe(json.loads(data))).encode()
            out.writestr(item, data)
        for name, data in (extra or {}).items():
            out.writestr(name, data)
    return destination


def _counts(client):
    config = client.app.container["config"]
    with client.app.container["session_factory"]() as db:
        rows = (
            db.query(Dataset).count(),
            db.query(ModelSession).count(),
            db.query(Run).count(),
            db.query(Metric).count(),
        )
    folders = tuple(
        sorted(p.name for p in Path(config[key]).glob("*"))
        if Path(config[key]).exists()
        else ()
        for key in ("DATASETS_PATH", "RUNS_PATH", "PREPROCESSING_PATH")
    )
    return rows, folders


def test_unique_name_keeps_a_free_name_and_numbers_a_taken_one():
    assert unique_name("iris", set()) == "iris"
    assert unique_name("iris", {"iris"}) == "iris (2)"
    assert unique_name("iris", {"iris", "iris (2)"}) == "iris (3)"


@pytest.mark.parametrize("case_name", ["classifier", "regressor"])
def test_a_round_trip_keeps_dataset_splits_recipe_and_metrics(
    request, client, tmp_path, case_name
):
    case = request.getfixturevalue(case_name)
    package = _export_all(client, case, tmp_path / "round-trip.dashai")

    result = _import(client, package)

    with client.app.container["session_factory"]() as db:
        original = db.get(ModelSession, case["session_id"])
        imported = db.get(ModelSession, result["session_id"])
        for field in SESSION_FIELDS[1:]:
            assert getattr(imported, field) == getattr(original, field), field
        assert imported.preprocessing_status == "ready"
        old_dataset = db.get(Dataset, original.dataset_id)
        new_dataset = db.get(Dataset, imported.dataset_id)
        for entry in ("data.arrow", "splits.json"):
            old = Path(old_dataset.file_path) / "dataset" / entry
            new = Path(new_dataset.file_path) / "dataset" / entry
            assert old.read_bytes() == new.read_bytes()
        assert new_dataset.total_rows == old_dataset.total_rows

        old_run = db.get(Run, case["trained"])
        (new_run_,) = imported.runs
        for field in RUN_FIELDS:
            assert getattr(new_run_, field) == getattr(old_run, field), field
        assert new_run_.status == RunStatus.FINISHED
        assert Path(new_run_.run_path).exists()
        assert new_run_.run_path != old_run.run_path

        def metric_rows(run_id):
            return sorted(
                (m.split.name, m.level.name, m.name, m.value)
                for m in db.query(Metric).filter(Metric.run_id == run_id)
            )

        assert metric_rows(new_run_.id) == metric_rows(old_run.id)


@pytest.mark.parametrize(
    ("case_name", "columns"),
    [("classifier", RAW_INPUT_COLUMNS), ("regressor", REGRESSION_INPUTS)],
)
def test_an_imported_run_predicts_what_the_original_predicts(
    request, client, tmp_path, case_name, columns
):
    case = request.getfixturevalue(case_name)
    result = _import(client, _export_all(client, case, tmp_path / "p.dashai"))
    with client.app.container["session_factory"]() as db:
        (imported_run,) = db.get(ModelSession, result["session_id"]).runs
        imported_run_id = imported_run.id

    expected = predicted_in_app(client, case["trained"], columns, n_rows=10)
    assert predicted_in_app(client, imported_run_id, columns, n_rows=10) == expected


def test_importing_twice_creates_numbered_copies_and_keeps_the_original(
    client, regressor, tmp_path
):
    package = _export_all(client, regressor, tmp_path / "twice.dashai")

    first = _import(client, package)
    second = _import(client, package)

    assert first["renamed"] == {"session": True, "dataset": True}
    assert first["session_name"].startswith("session-package-regressor-session (")
    assert first["dataset_name"].startswith("test_csv_1 (")
    assert len({first["session_name"], second["session_name"]}) == 2
    assert len({first["dataset_name"], second["dataset_name"]}) == 2
    with client.app.container["session_factory"]() as db:
        original = db.get(ModelSession, regressor["session_id"])
        assert original.name == "session-package-regressor-session"
        assert [run.id for run in original.runs] == [regressor["trained"]]


def test_a_recipe_only_import_is_ready_to_train(client, classifier, tmp_path):
    package = _export_all(
        client, classifier, tmp_path / "recipe.dashai", include_trained_models=False
    )

    result = _import(client, package)

    assert result["recipe_runs"] == ["Package KNeighborsClassifier"]
    with client.app.container["session_factory"]() as db:
        session = db.get(ModelSession, result["session_id"])
        (run,) = session.runs
        assert run.status == RunStatus.NOT_STARTED
        assert run.run_path is None
        assert db.query(Metric).filter(Metric.run_id == run.id).count() == 0
        # The preprocessing job ran (the test queue is immediate) and fitted it.
        assert session.preprocessing_status == "ready"
        assert (Path(session.preprocessing_artifacts_path) / "final.pkl").exists()


def _a_model_file(client, case, tmp_path):
    from DashAI.back.model_package.export import build_package

    destination = tmp_path / "model.dashai-model"
    build_package(
        case["trained"],
        destination,
        client.app.container["session_factory"],
        client.app.container["component_registry"],
    )
    return destination


@pytest.mark.parametrize(
    ("problem", "error"),
    [
        ("foreign", ModelPackageError),
        ("model_file", WrongPackageKindError),
        ("newer_format", UnsupportedPackageFormatError),
        ("missing_plugin", MissingPluginError),
        ("unknown_model", MissingPluginError),
    ],
)
def test_import_refuses_foreign_files_models_newer_formats_and_missing_plugins(
    client, regressor, tmp_path, problem, error
):
    package = _export_all(client, regressor, tmp_path / "source.dashai")
    broken = tmp_path / "broken.dashai"
    if problem == "foreign":
        with zipfile.ZipFile(broken, "w") as archive:
            archive.writestr("readme.txt", "hello")
    elif problem == "model_file":
        broken = _a_model_file(client, regressor, tmp_path)
    elif problem == "newer_format":
        _rewrite(package, broken, manifest=lambda m: {**m, "format_version": 99})
    elif problem == "missing_plugin":
        plugin = {"name": "dashai-plugin-that-does-not-exist", "version": "1.0"}
        _rewrite(package, broken, manifest=lambda m: {**m, "plugins": [plugin]})
    else:

        def unknown(recipe):
            recipe["runs"][0]["model_name"] = "NoSuchModel"
            return recipe

        _rewrite(package, broken, recipe=unknown)

    before = _counts(client)
    with pytest.raises(error):
        _import(client, broken)
    assert _counts(client) == before


def test_a_zip_slip_entry_is_refused_and_writes_nothing(client, regressor, tmp_path):
    package = _export_all(client, regressor, tmp_path / "source.dashai")
    escape = f"evil-{uuid.uuid4().hex}.txt"
    broken = _rewrite(
        package, tmp_path / "slip.dashai", extra={f"../{escape}": "owned"}
    )

    before = _counts(client)
    with pytest.raises(UnsafePackageError):
        _import(client, broken)
    assert not (Path(tempfile.gettempdir()) / escape).exists()
    assert _counts(client) == before


def test_a_failure_midway_leaves_no_rows_and_no_files(
    client, classifier, tmp_path, monkeypatch
):
    package = _export_all(client, classifier, tmp_path / "midway.dashai")

    def full_disk(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(session_load, "_copy_model", full_disk)
    before = _counts(client)
    with pytest.raises(OSError, match="No space"):
        _import(client, package)
    assert _counts(client) == before


def test_version_drift_is_reported_as_a_warning(client, regressor, tmp_path):
    package = _export_all(client, regressor, tmp_path / "source.dashai")

    def old_sklearn(manifest):
        manifest["versions"]["scikit-learn"] = "0.0.1"
        return manifest

    drifted = _rewrite(package, tmp_path / "drift.dashai", manifest=old_sklearn)

    result = _import(client, drifted)

    assert any("scikit-learn 0.0.1" in warning for warning in result["warnings"])


# Endpoints ------------------------------------------------------------------


def test_the_preview_endpoint_answers_404_for_a_missing_session(client):
    response = client.get("/api/v1/model-session/999999/export/preview")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_the_preview_endpoint_lists_the_runs(client, regressor):
    response = client.get(
        f"/api/v1/model-session/{regressor['session_id']}/export/preview"
    )
    assert response.status_code == 200, response.text
    assert [run["id"] for run in response.json()["runs"]] == [regressor["trained"]]


def test_the_export_endpoint_downloads_a_session_file(client, regressor, tmp_path):
    response = client.post(
        f"/api/v1/model-session/{regressor['session_id']}/export",
        json={"run_ids": [regressor["trained"]], "include_trained_models": True},
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-disposition"].endswith('.dashai"')
    package = tmp_path / "downloaded.dashai"
    package.write_bytes(response.content)
    _, manifest, _, _ = _read(package)
    assert manifest["kind"] == "session"


def test_the_export_endpoint_answers_409_without_runs(client, regressor):
    response = client.post(
        f"/api/v1/model-session/{regressor['session_id']}/export",
        json={"run_ids": []},
    )
    assert response.status_code == 409
    assert "at least one run" in response.json()["detail"]


def test_the_import_endpoint_creates_the_session(client, regressor, tmp_path):
    package = _export_all(client, regressor, tmp_path / "upload.dashai")

    with open(package, "rb") as handle:
        response = client.post(
            "/api/v1/model-session/import",
            files={"file": ("upload.dashai", handle, "application/zip")},
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["renamed"]["session"] is True
    session = client.get(f"/api/v1/model-session/{body['session_id']}")
    assert session.status_code == 200
    assert session.json()["name"] == body["session_name"]


def test_the_import_endpoint_answers_400_for_a_model_file(client, regressor, tmp_path):
    model_file = _a_model_file(client, regressor, tmp_path)

    with open(model_file, "rb") as handle:
        response = client.post(
            "/api/v1/model-session/import",
            files={"file": ("model.dashai-model", handle, "application/zip")},
        )

    assert response.status_code == 400
    assert "not a session file" in response.json()["detail"]


def test_the_import_endpoint_answers_409_for_a_newer_format(
    client, regressor, tmp_path
):
    package = _export_all(client, regressor, tmp_path / "source.dashai")
    newer = _rewrite(
        package,
        tmp_path / "newer.dashai",
        manifest=lambda m: {**m, "format_version": 99},
    )

    with open(newer, "rb") as handle:
        response = client.post(
            "/api/v1/model-session/import",
            files={"file": ("newer.dashai", handle, "application/zip")},
        )

    assert response.status_code == 409
    assert "Update DashAI" in response.json()["detail"]
