"""Unit that prepares a dataset for a task and splits it into train/val/test."""

import logging

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.splitter_scope import (
    SplitterScopeMixin,
    input_columns_field,
    output_columns_field,
    partition_splitter_field,
    task_name_field,
)

log = logging.getLogger(__name__)


class PrepareAndSplitSchema(BaseSchema):
    task_name: task_name_field()  # type: ignore
    input_columns: input_columns_field()  # type: ignore
    output_columns: output_columns_field()  # type: ignore
    splitter: partition_splitter_field()  # type: ignore


class PrepareAndSplitUnit(BaseUnit, SplitterScopeMixin):
    """Validate a dataset against a task and split it once into three partitions.

    Runs the task's own validation, counts the labels, separates features from
    targets and hands the pair to a holdout splitter.

    The split configuration is a component field rather than an untyped
    dictionary: which partitions exist, what they are called and what may be
    configured are the splitter's own schema, so the front renders that form
    instead of a free-form object nobody could validate.

    The sibling for cross-validation is ``PrepareAndFoldUnit``. They are two
    units and not one with a flag for two reasons that both bite. A component
    field carries a single ``parent`` and the front reads it directly off the
    property, so offering two families from one field leaves the user with no
    selector at all. And what comes back has a different *type* -- one
    ``DatasetDict`` against a list of them -- which a contract that compares
    key names cannot express: the same key holding two shapes would validate
    statically and fail at run time. The fold unit therefore publishes
    ``x_folds`` and ``y_folds`` rather than reusing ``x`` and ``y``.
    """

    SCHEMA = PrepareAndSplitSchema

    # dataset_id is declared even though it only decorates an error message:
    # an undeclared read is a contract a DAG validator cannot see, and the
    # loaders publish it precisely so downstream units can name their input.
    REQUIRES = ("dataset", "dataset_id")
    PROVIDES = ("x", "y", "n_labels", "task", "split_indexes", "task_name")

    def __init__(self, **config) -> None:
        super().__init__(**config)
        # Kept on the instance, never in the context: two of these units in one
        # context would otherwise overwrite each other's resolved task.
        self._task = None
        self._splitter_class = None

    def execute(self, ctx: ExecutionContext) -> None:
        dataset = ctx.require("dataset")
        dataset_id = ctx.require("dataset_id")

        task, n_labels, x, y = self._prepare(dataset, dataset_id)
        x, y, split_indexes = self._split(x, y)

        ctx.put_ref("task_name", self.config["task_name"])
        ctx.put_ref("split_indexes", split_indexes)
        ctx.put("task", task)
        ctx.put("n_labels", n_labels)
        ctx.put("x", x)
        ctx.put("y", y)
