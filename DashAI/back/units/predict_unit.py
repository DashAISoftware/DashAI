"""Unit that runs a trained model over a dataset and decodes its output."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import (
    BaseSchema,
    list_field,
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


class PredictSchema(BaseSchema):
    task_name: schema_field(
        string_field(),
        placeholder="TabularClassificationTask",
        description=MultilingualString(
            en="Name of the task that turns raw model output into labels.",
            es="Nombre de la tarea que convierte la salida cruda del modelo en "
            "etiquetas.",
            pt="Nome da tarefa que converte a saída bruta do modelo em rótulos.",
            de="Name der Aufgabe, die die Rohausgabe des Modells in Labels umwandelt.",
            zh="将模型原始输出转换为标签的任务名称。",
        ),
        alias=MultilingualString(
            en="Task", es="Tarea", pt="Tarefa", de="Aufgabe", zh="任务"
        ),
    )  # type: ignore
    input_columns: schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns handed to the model as input.",
            es="Nombres de las columnas entregadas al modelo como entrada.",
            pt="Nomes das colunas entregues ao modelo como entrada.",
            de="Namen der Spalten, die dem Modell als Eingabe übergeben werden.",
            zh="作为输入交给模型的列名。",
        ),
        alias=MultilingualString(
            en="Input columns",
            es="Columnas de entrada",
            pt="Colunas de entrada",
            de="Eingabespalten",
            zh="输入列",
        ),
    )  # type: ignore
    output_columns: schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns the model predicts. Only the first one is "
            "used: it names the column the predictions are written to.",
            es="Nombres de las columnas que el modelo predice. Solo se usa la "
            "primera: da nombre a la columna donde se escriben las predicciones.",
            pt="Nomes das colunas que o modelo prevê. Apenas a primeira é "
            "usada: dá nome à coluna onde as previsões são escritas.",
            de="Namen der Spalten, die das Modell vorhersagt. Nur die erste "
            "wird verwendet: sie benennt die Spalte für die Vorhersagen.",
            zh="模型预测的列名。仅使用第一个：它命名写入预测结果的列。",
        ),
        alias=MultilingualString(
            en="Output columns",
            es="Columnas de salida",
            pt="Colunas de saída",
            de="Ausgabespalten",
            zh="输出列",
        ),
    )  # type: ignore


class PredictUnit(BaseUnit):
    """Predict with a trained model and decode the result into labels.

    The input columns are selected against the dataset the context holds at
    this moment, never against a column list captured earlier: whatever built
    that dataset — a load from disk or hand-typed rows — is free to have
    produced a different shape.

    The training dataset is required rather than reloaded because the task
    decodes predicted class indexes against its labels. The model is handed the
    selected columns unprepared: models apply their own preprocessing inside
    ``predict``, and preparing beforehand would break the ones that replace
    their input columns with derived features.
    """

    SCHEMA = PredictSchema

    REQUIRES = ("dataset", "model", "train_dataset")
    PROVIDES = ("y_pred",)

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
        """Resolve the task before anything observable happens.

        The orchestrator calls this ahead of loading the model, which is what
        keeps a missing task reported as a task problem rather than being
        overtaken by whatever fails next.
        """
        self._resolve_task()

    def execute(self, ctx: ExecutionContext) -> None:
        import numpy as np

        task = self._resolve_task()

        dataset = ctx.require("dataset")
        model = ctx.require("model")
        train_dataset = ctx.require("train_dataset")

        prepared_dataset = dataset.select_columns(self.config["input_columns"])
        y_pred_proba = np.array(model.predict(prepared_dataset))
        y_pred = task.process_predictions(
            train_dataset, y_pred_proba, self.config["output_columns"][0]
        )

        ctx.put("y_pred", y_pred)
