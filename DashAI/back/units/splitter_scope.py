"""Shared body of the two units that prepare a dataset and partition it.

``PrepareAndSplitUnit`` and ``PrepareAndFoldUnit`` do the same four things --
resolve the task, prepare the dataset for it, separate features from targets,
and hand the pair to a splitter -- and differ only in which family of splitters
they offer and in the shape of what comes back. Keeping the body here is what
stops the two from drifting into two answers for the same dataset.

Named ``SplitterScopeMixin`` rather than ``BaseSomething`` on purpose: the
registry derives a component's type by walking its ``__mro__`` for a class whose
name contains "Base" and that declares ``TYPE``, and demands exactly one. A
shared parent called ``Base*`` would be a second candidate and would break the
registration of every unit that inherited it.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    component_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.splitters.base_splitter import BaseSplitter
    from DashAI.back.tasks.base_task import BaseTask

log = logging.getLogger(__name__)


def task_name_field():
    return schema_field(
        string_field(),
        placeholder="TabularClassificationTask",
        description=MultilingualString(
            en="Name of the task the dataset is prepared for.",
            es="Nombre de la tarea para la que se prepara el conjunto de datos.",
            pt="Nome da tarefa para a qual o conjunto de dados é preparado.",
            de="Name der Aufgabe, für die der Datensatz vorbereitet wird.",
            zh="数据集所准备的任务名称。",
        ),
        alias=MultilingualString(
            en="Task", es="Tarea", pt="Tarefa", de="Aufgabe", zh="任务"
        ),
    )


def input_columns_field():
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns used as model input.",
            es="Nombres de las columnas usadas como entrada del modelo.",
            pt="Nomes das colunas usadas como entrada do modelo.",
            de="Namen der als Modelleingabe verwendeten Spalten.",
            zh="用作模型输入的列名。",
        ),
        alias=MultilingualString(
            en="Input columns",
            es="Columnas de entrada",
            pt="Colunas de entrada",
            de="Eingabespalten",
            zh="输入列",
        ),
    )


def output_columns_field():
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns the model has to predict.",
            es="Nombres de las columnas que el modelo debe predecir.",
            pt="Nomes das colunas que o modelo deve prever.",
            de="Namen der Spalten, die das Modell vorhersagen soll.",
            zh="模型需要预测的列名。",
        ),
        alias=MultilingualString(
            en="Output columns",
            es="Columnas de salida",
            pt="Colunas de saída",
            de="Ausgabespalten",
            zh="输出列",
        ),
    )


def _splitter_field(parent: str, placeholder: Dict[str, Any]):
    """A splitter chosen from one family, with its own configuration.

    Parameters
    ----------
    parent : str
        Class name every offered splitter has in its ``__mro__``. The two
        families are told apart here rather than by a flag, because the front
        resolves the choices with ``component_parent``, which matches any
        ancestor by name: ``PartitionSplitter`` offers the two holdout
        splitters and ``FoldSplitter`` the eight fold ones, with no renaming
        and no change to the registry.
    placeholder : dict
        The ``{"component": …, "params": {…}}`` value the form starts on.
    """
    return schema_field(
        component_field(parent=parent),
        placeholder=placeholder,
        description=MultilingualString(
            en="Splitter that decides how the dataset is partitioned, along "
            "with its own configuration.",
            es="Particionador que decide cómo se divide el conjunto de datos, "
            "junto con su propia configuración.",
            pt="Divisor que decide como o conjunto de dados é particionado, "
            "junto com a sua própria configuração.",
            de="Splitter, der über die Aufteilung des Datensatzes entscheidet, "
            "samt seiner eigenen Konfiguration.",
            zh="决定数据集如何划分的划分器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Splitter",
            es="Particionador",
            pt="Divisor",
            de="Splitter",
            zh="划分器",
        ),
    )


def partition_splitter_field():
    """The field of the unit that splits once, offering the holdout family."""
    return _splitter_field(
        parent="PartitionSplitter",
        placeholder={
            "component": "HoldoutSplitter",
            "params": {
                "train": 0.6,
                "test": 0.2,
                "validation": 0.2,
                "stratify": False,
                "shuffle": True,
                "random_state": 42,
            },
        },
    )


def fold_splitter_field():
    """The field of the unit that splits into folds, offering the fold family."""
    return _splitter_field(
        parent="FoldSplitter",
        placeholder={
            "component": "KFoldSplitter",
            "params": {
                "n_splits": 5,
                "test_size": 0.1,
                "shuffle": True,
                "random_state": 42,
            },
        },
    )


class SplitterScopeMixin:
    """Prepare a dataset for a task and hand it to a splitter.

    Every method here takes and returns plain values and never touches the
    execution context. A ``ctx.put`` hidden in a shared helper is invisible to
    the audit that parses each unit's own source, so a broken ``PROVIDES``
    would pass it.
    """

    #: Declared here so both the memoizing helpers and a reader can see what
    #: state an instance carries; each unit sets them in its own ``__init__``,
    #: because ``BaseUnit.__init__`` comes first in the MRO and does not chain.
    _task = None
    _splitter_class = None

    @property
    def splitter_name(self) -> str:
        return self.config["splitter"]["component"]

    @property
    def splitter_params(self) -> Dict[str, Any]:
        return self.config["splitter"]["params"]

    def _resolve_task(self) -> "BaseTask":
        """Instantiate the task, memoized on this unit.

        On the instance rather than in the context: a context can hold two of
        these units, and a context-global cache would silently give the second
        one the first one's task.
        """
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

    def _resolve_splitter(self) -> "BaseSplitter":
        """Build the configured splitter.

        ``BaseSplitter.__init__`` takes a single ``splits_data`` mapping rather
        than keyword arguments, so this is the one component field in the units
        that is not expanded with ``**params``. The shape is the splitter's own
        schema either way; only how it is handed over differs.
        """
        from kink import di

        splitter_name = self.splitter_name
        if self._splitter_class is None:
            try:
                self._splitter_class = di["component_registry"][splitter_name]["class"]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Splitter with name {splitter_name} in registry.",
                ) from e

        try:
            return self._splitter_class(splits_data=dict(self.splitter_params))
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error instantiating splitter {splitter_name}, {e}",
            ) from e

    def _prepare(
        self, dataset: "DashAIDataset", dataset_id: Any
    ) -> Tuple["BaseTask", int, "DashAIDataset", "DashAIDataset"]:
        """Validate the dataset against the task and separate x from y.

        Returns
        -------
        tuple
            The task, the number of labels, and the input and output datasets,
            in that order. Nothing here is written to the context: the unit
            that called this decides what it promises.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import select_columns

        task = self._resolve_task()
        task_name: str = self.config["task_name"]
        input_columns: List[str] = self.config["input_columns"]
        output_columns: List[str] = self.config["output_columns"]

        try:
            prepared_dataset = task.prepare_for_task(
                dataset=dataset,
                input_columns=input_columns,
                output_columns=output_columns,
            )
            n_labels = task.num_labels(prepared_dataset, output_columns[0])
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not prepare Dataset {dataset_id} for Task {task_name}",
            ) from e

        try:
            # Read from the prepared dataset rather than the loaded one: a task
            # may reorder the rows, and forecasting does, sorting them by date
            # so a temporal splitter carves real periods of time. Selecting
            # from the loaded dataset would drop that work on the floor.
            x, y = select_columns(prepared_dataset, input_columns, output_columns)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error selecting input and output columns from dataset {dataset_id}",
            ) from e

        return task, n_labels, x, y

    def _split(self, x: "DashAIDataset", y: "DashAIDataset"):
        """Partition the pair with the configured splitter.

        The splitter's own complaint is passed through as the whole message,
        undecorated. It already names the numbers that explain the refusal --
        how many folds against how many rows -- and a caller that wants to say
        which run this was frames it from outside, which is how the message
        the user reads is built today.
        """
        splitter = self._resolve_splitter()
        try:
            return splitter.split(x, y)
        except JobError:
            raise
        except Exception as e:
            log.exception(e)
            raise JobError(str(e)) from e
