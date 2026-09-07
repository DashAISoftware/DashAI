"""Tests for explorer plot override persistence and reset."""

import json
import pathlib

from DashAI.back.core.enums.status import ExplorerStatus
from DashAI.back.dependencies.database.models import Dataset, Explorer, Notebook
from DashAI.back.exploration.artifact_store import write_artifacts

ORIGINAL_FIGURE = {
    "data": [{"y": [1, 2, 3], "type": "bar"}],
    "layout": {"title": "original"},
}
EDITED_FIGURE = {
    "data": [{"y": [1, 2, 3], "type": "bar"}],
    "layout": {"title": "edited"},
}


def _make_explorer(client, tmp_path_name="explorer_artifacts"):
    """Create a finished explorer row with one stored plotly artifact.

    Parameters
    ----------
    client : TestClient
        The app test client, used to reach the app's session factory and
        local path.
    tmp_path_name : str
        Subdirectory name under the app local path holding the artifacts.

    Returns
    -------
    tuple
        ``(explorer_id, artifacts_path)``.
    """
    services = client.app.container._services
    session_factory = services["session_factory"]
    local_path = pathlib.Path(services["config"]["LOCAL_PATH"])

    with session_factory() as db:
        dataset = Dataset(name=f"ds-{tmp_path_name}", file_path="/tmp/ds")
        db.add(dataset)
        db.commit()
        notebook = Notebook(dataset_id=dataset.id, file_path="/tmp/nb")
        db.add(notebook)
        db.commit()
        explorer = Explorer(
            notebook_id=notebook.id,
            columns=[],
            exploration_type="TestExplorer",
            parameters={},
            status=ExplorerStatus.FINISHED,
        )
        db.add(explorer)
        db.commit()
        explorer_id = explorer.id

        artifacts_path = local_path / tmp_path_name / f"{explorer_id}_artifacts.json"
        write_artifacts(
            artifacts_path,
            [
                {
                    "type": "plotly",
                    "payload": json.dumps(ORIGINAL_FIGURE),
                    "title": "Plot",
                    "role": "explanation",
                    "index": 0,
                }
            ],
        )
        explorer.artifacts_path = artifacts_path.as_posix()
        db.commit()

    return explorer_id, artifacts_path


def test_explorer_model_has_plot_overrides_column(client):
    """The explorer table stores plot overrides."""
    explorer_id, _ = _make_explorer(client, "col_check")
    session_factory = client.app.container._services["session_factory"]

    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        explorer.plot_overrides = {"0": json.dumps(EDITED_FIGURE)}
        db.commit()

    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        assert json.loads(explorer.plot_overrides["0"]) == EDITED_FIGURE


def test_put_stores_override_without_touching_artifacts_file(client):
    """Saving an edit writes an override and leaves the stored figure intact."""
    explorer_id, artifacts_path = _make_explorer(client, "put_check")
    before = artifacts_path.read_text(encoding="utf-8")

    response = client.put(
        f"/api/v1/explorer/{explorer_id}/results/",
        json={"index": 0, "figure": EDITED_FIGURE},
    )

    assert response.status_code == 200
    assert artifacts_path.read_text(encoding="utf-8") == before

    session_factory = client.app.container._services["session_factory"]
    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        assert json.loads(explorer.plot_overrides["0"]) == EDITED_FIGURE


def test_results_returns_override_flagged_as_overridden(client):
    """The read endpoint serves the edited figure and flags it."""
    explorer_id, _ = _make_explorer(client, "read_check")
    client.put(
        f"/api/v1/explorer/{explorer_id}/results/",
        json={"index": 0, "figure": EDITED_FIGURE},
    )

    response = client.post(
        f"/api/v1/explorer/{explorer_id}/results/", json={"options": {}}
    )

    assert response.status_code == 200
    artifact = response.json()[0]
    assert json.loads(artifact["payload"]) == EDITED_FIGURE
    assert artifact["overridden"] is True


def test_delete_override_restores_the_computed_figure(client):
    """Reset drops the override so the original figure is served again."""
    explorer_id, _ = _make_explorer(client, "reset_check")
    client.put(
        f"/api/v1/explorer/{explorer_id}/results/",
        json={"index": 0, "figure": EDITED_FIGURE},
    )

    response = client.delete(f"/api/v1/explorer/{explorer_id}/results/override/0")
    assert response.status_code == 200

    results = client.post(
        f"/api/v1/explorer/{explorer_id}/results/", json={"options": {}}
    ).json()
    assert json.loads(results[0]["payload"]) == ORIGINAL_FIGURE
    assert "overridden" not in results[0]

    session_factory = client.app.container._services["session_factory"]
    with session_factory() as db:
        assert db.get(Explorer, explorer_id).plot_overrides is None


def test_delete_missing_override_is_a_no_op(client):
    """Resetting an artifact that was never edited succeeds."""
    explorer_id, _ = _make_explorer(client, "noop_check")

    response = client.delete(f"/api/v1/explorer/{explorer_id}/results/override/3")

    assert response.status_code == 200


def test_override_endpoints_404_on_unknown_explorer(client):
    """Both override endpoints reject an explorer id that does not exist."""
    assert (
        client.put(
            "/api/v1/explorer/999999/results/",
            json={"index": 0, "figure": EDITED_FIGURE},
        ).status_code
        == 404
    )
    assert (
        client.delete("/api/v1/explorer/999999/results/override/0").status_code == 404
    )
