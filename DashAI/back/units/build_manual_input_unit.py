"""Unit that turns hand-typed rows into a dataset to predict on."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import (
    BaseSchema,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.tasks.base_task import BaseTask

log = logging.getLogger(__name__)


class BuildManualInputSchema(BaseSchema):
    task_name: schema_field(
        string_field(),
        placeholder="TabularClassificationTask",
        description=MultilingualString(
            en="Name of the task that validates and types the hand-typed rows.",
            es="Nombre de la tarea que valida y tipa las filas ingresadas a mano.",
            pt="Nome da tarefa que valida e tipa as linhas introduzidas à mão.",
            de="Name der Aufgabe, die die manuell eingegebenen Zeilen prüft "
            "und typisiert.",
            zh="用于校验并确定手工输入行类型的任务名称。",
        ),
        alias=MultilingualString(
            en="Task", es="Tarea", pt="Tarefa", de="Aufgabe", zh="任务"
        ),
    )  # type: ignore
    manual_input_data: schema_field(
        list,
        placeholder=[],
        description=MultilingualString(
            en="Rows to predict on, each a mapping from input column name to "
            "value. Uploaded files arrive as a path reference instead of bytes.",
            es="Filas a predecir, cada una un mapeo de nombre de columna de "
            "entrada a valor. Los archivos subidos llegan como una referencia "
            "a una ruta en vez de bytes.",
            pt="Linhas a prever, cada uma um mapeamento de nome de coluna de "
            "entrada para valor. Os ficheiros carregados chegam como uma "
            "referência a um caminho em vez de bytes.",
            de="Zu prognostizierende Zeilen, je eine Zuordnung von "
            "Eingabespaltenname zu Wert. Hochgeladene Dateien kommen als "
            "Pfadverweis statt als Bytes an.",
            zh="要预测的行，每行是输入列名到值的映射。上传的文件以路径引用而非字节形式传入。",
        ),
        alias=MultilingualString(
            en="Manual input",
            es="Entrada manual",
            pt="Entrada manual",
            de="Manuelle Eingabe",
            zh="手动输入",
        ),
    )  # type: ignore


class BuildManualInputUnit(BaseUnit):
    """Build the dataset to predict on from values the user typed in.

    The counterpart of loading one from disk: it produces the same ``dataset``
    key, so whatever runs next cannot tell the two apart. That is what lets the
    prediction step be written once for both sources.

    The task does the work — it is the task that knows the expected column
    types and how to turn an uploaded file into a cell — so this unit only
    resolves it and hands over the rows.
    """

    SCHEMA = BuildManualInputSchema

    PROVIDES = ("dataset",)
    RUNTIME_PARAMS = ("train_dataset_file_path",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._task = None

    def _resolve_task(self) -> "BaseTask":
        """Instantiate the task from the registry, memoized on this unit."""
        if self._task is not None:
            return self._task

        from kink import di

        component_registry = di["component_registry"]
        task_name = self.config["task_name"]

        try:
            task: "BaseTask" = component_registry[task_name]["class"]()
        except Exception as e:
            log.exception(e)
            raise JobError(f"Task {task_name} not found in the registry") from e

        self._task = task
        return task

    def validate(self, ctx: ExecutionContext) -> None:
        """Resolve the task before anything observable happens."""
        self._resolve_task()

    def execute(self, ctx: ExecutionContext) -> None:
        from pathlib import Path

        task = self._resolve_task()

        train_dataset_path = str(
            Path(f"{self.config['train_dataset_file_path']}/dataset/")
        )
        rows = self.config["manual_input_data"]

        ctx.put("dataset", task.process_manual_input(rows, train_dataset_path))
