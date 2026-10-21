"""Unit that prepares a dataset for a task that has no target column."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema, bool_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.splitter_scope import input_columns_field, task_name_field

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.tasks.base_task import BaseTask

log = logging.getLogger(__name__)


def standardise_field():
    return schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether every numeric input column with any variance is centred "
            "and scaled before the model sees it. Models that measure distances "
            "are otherwise dominated by the column with the widest range.",
            es="Si cada columna numérica de entrada con varianza se centra y se "
            "escala antes de que la vea el modelo. Si no, los modelos que miden "
            "distancias quedan dominados por la columna de mayor rango.",
            pt="Se cada coluna numérica de entrada com variância é centrada e "
            "escalada antes de o modelo a ver. Caso contrário, os modelos que "
            "medem distâncias ficam dominados pela coluna de maior amplitude.",
            de="Ob jede numerische Eingabespalte mit Varianz zentriert und "
            "skaliert wird, bevor das Modell sie sieht. Sonst dominiert bei "
            "distanzbasierten Modellen die Spalte mit der größten Spannweite.",
            zh="是否在模型使用前对每个有方差的数值输入列进行中心化和缩放。"
            "否则，基于距离的模型会被取值范围最大的列主导。",
        ),
        alias=MultilingualString(
            en="Standardise",
            es="Estandarizar",
            pt="Padronizar",
            de="Standardisieren",
            zh="标准化",
        ),
    )


class PrepareWithoutTargetSchema(BaseSchema):
    task_name: task_name_field()  # type: ignore
    input_columns: input_columns_field()  # type: ignore
    standardise: standardise_field()  # type: ignore


def standardise_features(x: "DashAIDataset") -> "DashAIDataset":
    """Centre and scale the numeric columns of a dataset that have variance.

    Every clustering algorithm DashAI ships measures distances, so a column
    expressed in a wider unit dominates the ones next to it. On a dataset
    holding scores from 0 to 100 beside hours from 1 to 11, DBSCAN's default eps
    of 0.5 labels every row as noise and Spectral's RBF affinity underflows to
    an empty graph.

    Columns with no variance are left alone, since dividing them by a zero
    standard deviation is what produces the NaNs the models then reject. A
    dataset with nothing to scale is returned as the same object.

    Parameters
    ----------
    x : DashAIDataset
        Input features, restricted to the session's input columns.

    Returns
    -------
    DashAIDataset
        The same dataset with its numeric columns standardised.
    """
    from sklearn.preprocessing import StandardScaler

    from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

    frame = x.to_pandas()
    numeric = frame.select_dtypes(include=["number"]).columns
    movable = [c for c in numeric if frame[c].std(ddof=0) > 0]
    if not movable:
        return x

    frame = frame.copy()
    frame[movable] = StandardScaler().fit_transform(frame[movable])
    return to_dashai_dataset(frame)


class PrepareWithoutTargetUnit(BaseUnit):
    """Prepare a dataset for a task that declares no target column.

    The counterpart of ``PrepareAndSplitUnit`` for tasks whose
    ``REQUIRES_TARGET`` is False, such as clustering. It validates the dataset
    against the task, keeps the input columns and, unless told not to,
    standardises them. Nothing is partitioned: such a task is fitted and scored
    over every row, because there is nothing held out to evaluate against.

    It publishes the features under their own key, ``features``, a single
    dataset, rather than reusing ``x``: ``x`` is a dict of partitions, and the
    name of a key is part of its contract. A graph validator compares names, so
    a reused name with a different shape would let a wrong edge through.

    ``n_labels`` is the task's answer to how many labels there are, which for a
    task without a target is ``None`` -- the same value a regression task gives.
    It is published so the unit that builds the model is fed the same way for
    both kinds of task.
    """

    SCHEMA = PrepareWithoutTargetSchema

    REQUIRES = ("dataset", "dataset_id")
    PROVIDES = ("features", "n_labels", "task_name")

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._task = None

    def _resolve_task(self) -> "BaseTask":
        """Instantiate the task, memoized on this unit rather than the context."""
        if self._task is not None:
            return self._task

        from kink import di

        task_name: str = self.config["task_name"]
        try:
            self._task = di["component_registry"][task_name]["class"]()
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Task with name {task_name} in registry",
            ) from e
        return self._task

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_dataset import select_columns

        dataset = ctx.require("dataset")
        dataset_id = ctx.require("dataset_id")
        task_name: str = self.config["task_name"]
        input_columns = self.config["input_columns"]
        task = self._resolve_task()

        try:
            prepared = task.prepare_for_task(
                dataset=dataset,
                input_columns=input_columns,
                output_columns=[],
            )
            features, _ = select_columns(prepared, input_columns, [])
            if self.config.get("standardise", True):
                features = standardise_features(features)
            n_labels = task.num_labels(prepared)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not prepare Dataset {dataset_id} for Task {task_name}",
            ) from e

        ctx.put("features", features)
        ctx.put("n_labels", n_labels)
        ctx.put_ref("task_name", task_name)
