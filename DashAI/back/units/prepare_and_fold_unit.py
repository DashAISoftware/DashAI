"""Unit that prepares a dataset for a task and carves it into folds."""

import logging

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.splitter_scope import (
    SplitterScopeMixin,
    fold_splitter_field,
    input_columns_field,
    output_columns_field,
    task_name_field,
)

log = logging.getLogger(__name__)


class PrepareAndFoldSchema(BaseSchema):
    task_name: task_name_field()  # type: ignore
    input_columns: input_columns_field()  # type: ignore
    output_columns: output_columns_field()  # type: ignore
    splitter: fold_splitter_field()  # type: ignore


class PrepareAndFoldUnit(BaseUnit, SplitterScopeMixin):
    """Validate a dataset against a task and carve it into cross-validation folds.

    The sibling of ``PrepareAndSplitUnit``, sharing its whole body. The two
    differ in which family of splitters they offer and, because of that, in the
    shape of what they publish.

    **What comes back is a list, and that is why the keys are different.** A
    fold splitter returns one entry per fold plus a trailing entry that is not
    a fold: its train partition is every row the folds could use and its test
    partition holds the rows reserved for scoring the model that gets kept,
    empty when the session reserved none. Publishing that list as ``x`` would
    give one key two possible types, which a contract comparing key names
    cannot express -- a graph would validate and then fail at run time, or
    worse, quietly train on the wrong thing. So it is ``x_folds`` and
    ``y_folds``.

    ``split_indexes`` keeps its name because it keeps its meaning -- the rows
    of every partition this run produced -- even though a fold payload is
    shaped differently from a holdout one. Which shape it is, is answered by
    asking the splitter that produced it, not by inspecting the payload.
    """

    SCHEMA = PrepareAndFoldSchema

    REQUIRES = ("dataset", "dataset_id")
    PROVIDES = ("x_folds", "y_folds", "n_labels", "task", "split_indexes", "task_name")

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
        x_folds, y_folds, split_indexes = self._split(x, y)

        ctx.put_ref("task_name", self.config["task_name"])
        ctx.put_ref("split_indexes", split_indexes)
        ctx.put("task", task)
        ctx.put("n_labels", n_labels)
        ctx.put("x_folds", x_folds)
        ctx.put("y_folds", y_folds)
