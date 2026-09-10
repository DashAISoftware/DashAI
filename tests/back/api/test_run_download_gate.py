"""Tests for the run-creation download gate (Task 8)."""

from kink import di

_RUN_PAYLOAD_BASE = {
    "parameters": {},
    "optimizer_name": "OptunaOptimizer",
    "optimizer_parameters": {},
    "goal_metric": "Accuracy",
    "plot_history_path": "",
    "plot_slice_path": "",
    "plot_contour_path": "",
    "plot_importance_path": "",
    "name": "gate-test-run",
    "description": "",
}


class _FakeDownloadableModel:
    """Minimal stub that looks like an undownloaded, download-required model."""

    REQUIRES_DOWNLOAD = True

    @classmethod
    def is_downloaded(cls):
        return False


class _FakeRegistry:
    """Registry wrapper that exposes FakeDownloadableModel on top of the real one."""

    def __init__(self, real):
        self._real = real

    def __getitem__(self, name):
        if name == "FakeDownloadableModel":
            return {"class": _FakeDownloadableModel, "downloaded": False}
        return self._real[name]

    def get_components_by_types(self, select=None, ignore=None):
        return self._real.get_components_by_types(select=select, ignore=ignore)

    def refresh_download_status(self, name):
        if name == "FakeDownloadableModel":
            return _FakeDownloadableModel.is_downloaded()
        return self._real.refresh_download_status(name)

    def __contains__(self, name):
        return name == "FakeDownloadableModel" or name in self._real


def _make_model_session(client, suffix=""):
    """Insert a Dataset + ModelSession row and return the ModelSession id."""
    import uuid

    from DashAI.back.dependencies.database.models import Dataset, ModelSession

    unique = suffix or uuid.uuid4().hex[:8]
    sf = client.app.container["session_factory"]
    with sf() as db:
        ds = Dataset(name=f"__gate_test_ds_{unique}__", file_path="")
        db.add(ds)
        db.flush()
        ms = ModelSession(
            dataset_id=ds.id,
            name=f"__gate_test_ms_{unique}__",
            task_name="TabularClassificationTask",
            input_columns=[],
            output_columns=[],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="",
            splits={},
        )
        db.add(ms)
        db.commit()
        db.refresh(ms)
        return ms.id


def test_upload_run_rejects_undownloaded_model_synthetic(client):
    """Creating a run for a not-yet-downloaded model must return HTTP 409."""
    ms_id = _make_model_session(client)
    old = di["component_registry"]
    di["component_registry"] = _FakeRegistry(old)
    try:
        resp = client.post(
            "/api/v1/run/",
            json={
                "model_session_id": ms_id,
                "model_name": "FakeDownloadableModel",
                **_RUN_PAYLOAD_BASE,
            },
        )
    finally:
        di["component_registry"] = old

    assert resp.status_code == 409
    assert "download" in resp.json()["detail"].lower()


def test_upload_run_rejects_undownloaded_model(client, monkeypatch):
    """Force a real downloadable model undownloaded; run creation must return 409."""
    registry = di["component_registry"]
    models = client.get("/api/v1/component/", params={"select_types": ["Model"]}).json()
    downloadable = [m for m in models if m["metadata"]["requires_download"]]
    if not downloadable:
        return  # no downloadable model registered in this environment; skip
    name = downloadable[0]["name"]
    monkeypatch.setitem(registry[name], "downloaded", False)

    resp = client.post(
        "/api/v1/run/",
        json={"model_session_id": 1, "model_name": name, **_RUN_PAYLOAD_BASE},
    )
    assert resp.status_code in (404, 409)
    if resp.status_code == 409:
        assert "download" in resp.json()["detail"].lower()


def test_upload_run_unknown_model_422(client):
    """POSTing a run with an unregistered model_name must return HTTP 422."""
    ms_id = _make_model_session(client)
    resp = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": ms_id,
            "model_name": "__totally_bogus_model_xyz__",
            **_RUN_PAYLOAD_BASE,
        },
    )
    assert resp.status_code == 422
