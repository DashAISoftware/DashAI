import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.evaluation.cv import CrossValidationEvaluationStrategy
from DashAI.back.evaluation.full_dataset import FullDatasetEvaluationStrategy
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.tasks.clustering_task import ClusteringTask
from DashAI.back.tasks.supervised_task import SupervisedTask
from DashAI.back.tasks.unsupervised_task import UnsupervisedTask

NUMERIC_SCHEMA = {
    "study_hours": {"type": "Float", "dtype": "float64"},
    "exam_score": {"type": "Float", "dtype": "float64"},
    "cohort": {"type": "Categorical", "dtype": "string"},
}


def _dataset():
    frame = pd.DataFrame(
        {
            "study_hours": [1.0, 2.0, 8.0, 9.0],
            "exam_score": [40.0, 45.0, 90.0, 95.0],
            "cohort": ["a", "a", "b", "b"],
        }
    )
    return transform_dataset_with_schema(to_dashai_dataset(frame), NUMERIC_SCHEMA)


# --- what the session screen reads -------------------------------------------


def test_clustering_needs_no_target_column():
    assert ClusteringTask.REQUIRES_TARGET is False
    assert SupervisedTask.REQUIRES_TARGET is True


def test_clustering_is_offered_only_the_strategy_that_carves_nothing():
    """The wizard lists the strategies related to the task and reads their
    kind, so this pairing is what leaves the splitter out of a clustering
    session, and what ModelJob relies on to chain the units without a target."""
    assert "ClusteringTask" in FullDatasetEvaluationStrategy.COMPATIBLE_COMPONENTS
    assert FullDatasetEvaluationStrategy.KIND == "full"
    for strategy in (HoldoutEvaluationStrategy, CrossValidationEvaluationStrategy):
        assert "ClusteringTask" not in strategy.COMPATIBLE_COMPONENTS


def test_the_metadata_sent_to_the_frontend_says_there_is_no_target():
    """The screen hides the output column picker on this key."""
    assert ClusteringTask.get_metadata()["requires_target"] is False


def test_clustering_declares_no_output_columns():
    metadata = ClusteringTask.get_metadata()

    assert metadata["outputs_cardinality"] == 0
    assert metadata["outputs_types"] == []
    assert metadata["inputs_cardinality"] == "n"


def test_clustering_is_an_unsupervised_task():
    assert issubclass(ClusteringTask, UnsupervisedTask)
    assert not issubclass(ClusteringTask, SupervisedTask)


# --- dataset validation ------------------------------------------------------


def test_a_numeric_dataset_with_no_output_column_is_accepted():
    ClusteringTask().validate_dataset_for_task(
        dataset=_dataset(),
        dataset_name="students",
        input_columns=["study_hours", "exam_score"],
        output_columns=[],
    )


def test_a_missing_output_column_list_is_treated_as_none_given():
    """The session sends no outputs at all for a task that needs no target."""
    ClusteringTask().validate_dataset_for_task(
        dataset=_dataset(),
        dataset_name="students",
        input_columns=["study_hours", "exam_score"],
        output_columns=None,
    )


def test_naming_an_output_column_is_refused():
    """``outputs_types`` is empty, so no column type is allowed as a target and
    the refusal lands on the type check before cardinality is ever reached."""
    with pytest.raises(TypeError, match="not an allowed type for output columns"):
        ClusteringTask().validate_dataset_for_task(
            dataset=_dataset(),
            dataset_name="students",
            input_columns=["study_hours"],
            output_columns=["exam_score"],
        )


def test_a_categorical_input_column_is_refused():
    """Every algorithm registered for this task measures numeric distances."""
    with pytest.raises(TypeError):
        ClusteringTask().validate_dataset_for_task(
            dataset=_dataset(),
            dataset_name="students",
            input_columns=["study_hours", "cohort"],
            output_columns=[],
        )
