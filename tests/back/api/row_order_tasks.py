"""Tasks for the tests that ask which rows a session reads, and in which order.

Training validates the dataset against the task and partitions what the task
hands back, and a task may reorder the rows: forecasting sorts them by date.
Every consumer of a run's row indexes therefore has to index the prepared
dataset, not the loaded one, and with any task that keeps the order the two
are the same rows and no test can tell them apart. ``ReversingTask`` is the
smallest reordering that does.

The registry only offers a task the components that are related to it, and
the session and run APIs refuse the rest. Like any task added from outside,
these name their strategies, splitters and models themselves: the built-in
components list only the built-in tasks. Relations are stored both ways, so a
task naming a splitter is enough for the splitter to be offered to it.
"""

from DashAI.back.tasks.regression_task import RegressionTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


class ReversingTask(TabularClassificationTask):
    """A task whose preparation hands the rows back in reverse order."""

    COMPATIBLE_COMPONENTS = [
        "HoldoutEvaluationStrategy",
        "CrossValidationEvaluationStrategy",
        "HoldoutSplitter",
        "KFoldSplitter",
        "KNeighborsClassifier",
    ]

    def prepare_for_task(self, dataset, input_columns, output_columns):
        prepared = super().prepare_for_task(dataset, input_columns, output_columns)
        return prepared.select(range(len(prepared) - 1, -1, -1))


class SeriesOnlyTask(RegressionTask):
    """A task that only a splitter which never shuffles may partition.

    It stands in for forecasting, whose only holdout splitter is the temporal
    one, without registering ``ForecastingTask`` itself: the default splitter
    a payload falls back to when it names none is ``HoldoutSplitter``, which
    shuffles, and this task does not offer it.
    """

    COMPATIBLE_COMPONENTS = [
        "HoldoutEvaluationStrategy",
        "TemporalHoldoutSplitter",
    ]
