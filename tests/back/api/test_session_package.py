"""Exporting a model session as a .dashai file and importing it back."""

import hashlib
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import Dataset, Run
from DashAI.back.session_package.export import (
    SessionNotExportableError,
    SessionNotFoundError,
    build_session_package,
    export_preview,
)
from tests.back.api.trained_runs import (
    add_metrics,
    fit_classifier_behind_preprocessing,
    fit_regressor,
    new_run,
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
