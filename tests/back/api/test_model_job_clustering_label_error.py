"""A clustering run whose labels cannot be read fails as a training failure.

The regression net pins the degenerate clustering and the failing metric, the
other two failures that can happen while a fitted clustering is scored, but not
this one. To the user the labels are what training produced, so the text stays
the one it always had, "Model training failed ...", wrapped by the job like
every training failure. Asserted on the whole message, prefix included, so a
wrapper that unified the three failures under one text would show.
"""

import pytest

from DashAI.back.dependencies.database.models import Metric, Run
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_job import ModelJob
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering
from tests.back.api.test_model_job_clustering_net import (
    _create_run,
    fixture_blobs_dataset,  # noqa: F401
    fixture_csv_dir,  # noqa: F401
    fixture_session,  # noqa: F401
)


def test_labels_that_cannot_be_read_are_reported_as_a_training_failure(
    client, session_id, monkeypatch
):
    def fail(self, x=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(KMeansClustering, "get_cluster_labels", fail)
    run_id = _create_run(client, session_id, "KMeansClustering", {"n_clusters": 3})

    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()

    assert str(raised.value) == (
        "Model training and evaluation failed Model training failed boom"
    )

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, run_id)
        assert run.run_path is None
        assert db.query(Metric).filter(Metric.run_id == run_id).count() == 0
