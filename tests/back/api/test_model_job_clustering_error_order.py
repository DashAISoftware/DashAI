"""Which error a clustering run reports when more than one thing is wrong.

The regression net pins one failure at a time, so it cannot see the order in
which they are checked. That order changed on purpose when the target free path
started building its model through ``BuildModelUnit``: the model is now checked
before the dataset is prepared, as it is for every supervised run. Before, a run
with both an unknown model and a dataset the task could not take reported the
dataset. This pins the new answer.
"""

import pytest

from DashAI.back.dependencies.database.models import Run
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_job import ModelJob
from tests.back.api.test_model_job_clustering_net import (
    NUMERIC_SCHEMA,
    _create_dataset,
    _create_session,
    fixture_csv_dir,  # noqa: F401
)


def test_an_unknown_model_is_reported_before_a_dataset_the_task_cannot_take(
    client, csv_dir
):
    dataset_id = _create_dataset(
        client,
        csv_dir / "blobs_with_category.csv",
        "blobs with category, error order",
        {**NUMERIC_SCHEMA, "group": {"type": "Categorical", "dtype": "string"}},
    )
    session_id = _create_session(
        client, dataset_id, "clustering error order", ["hours", "score", "group"]
    )

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=session_id,
            model_name="NotAClusteringModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={},
            goal_metric="",
            name="error order run",
        )
        db.add(run)
        db.commit()
        run_id = run.id

    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()

    assert str(raised.value) == (
        f"Error preparing dataset and components for run {run_id}: "
        "Unable to find Model with name NotAClusteringModel in registry."
    )
