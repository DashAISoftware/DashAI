"""Unit that rebuilds a run's train/test/val splits for an explanation."""

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
from DashAI.back.units.explanation_artifacts import load_persisted_preprocessor

if TYPE_CHECKING:
    from DashAI.back.tasks.base_task import BaseTask

log = logging.getLogger(__name__)


def _columns_field(alias: MultilingualString, description: MultilingualString):
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=description,
        alias=alias,
    )


class PrepareExplanationDataSchema(BaseSchema):
    task_name: schema_field(
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
    )  # type: ignore
    input_columns: _columns_field(
        alias=MultilingualString(
            en="Input columns",
            es="Columnas de entrada",
            pt="Colunas de entrada",
            de="Eingabespalten",
            zh="输入列",
        ),
        description=MultilingualString(
            en="Names of the columns used as model input.",
            es="Nombres de las columnas usadas como entrada del modelo.",
            pt="Nomes das colunas usadas como entrada do modelo.",
            de="Namen der als Modelleingabe verwendeten Spalten.",
            zh="用作模型输入的列名。",
        ),
    )  # type: ignore
    output_columns: _columns_field(
        alias=MultilingualString(
            en="Output columns",
            es="Columnas de salida",
            pt="Colunas de saída",
            de="Ausgabespalten",
            zh="输出列",
        ),
        description=MultilingualString(
            en="Names of the columns the model predicts.",
            es="Nombres de las columnas que el modelo predice.",
            pt="Nomes das colunas que o modelo prevê.",
            de="Namen der Spalten, die das Modell vorhersagt.",
            zh="模型需要预测的列名。",
        ),
    )  # type: ignore


class PrepareExplanationDataUnit(BaseUnit):
    """Rebuild the exact train/test/val split the run was trained on.

    Deliberately not ``PrepareAndSplitUnit``: that one *computes* a split from
    a ratio configuration, which would hand the explainer different rows than
    the model ever saw. This one replays the row indexes the run recorded, so
    the explanation is about the model that exists.

    Features stay unprepared — models apply their own preprocessing inside
    ``predict``, and preparing beforehand would break the ones that replace
    their input columns with derived features — while targets are encoded,
    because explainers compare them against the model's class indexes.

    Session preprocessing is another matter: converters the session fitted
    ahead of training (``PreprocessingJob``) are not part of the model, and
    the input columns the session records are the names they produced. When
    ``preprocessing_artifacts_path`` is supplied, the run's split is cut
    first and the persisted ``final.pkl`` is applied to each part, so the
    explainer's data is in the feature space the model was trained on. Cutting
    first keeps the run's indexes valid when a step removes rows
    (NanRemover), and no part is resampled, so no synthetic rows get in. The
    transformed dataset stays local to this unit: ``dataset`` in the context
    is left as it was loaded, since nothing downstream reads it and a unit
    that rewrote a key it requires would blur what it consumes and what it
    produces.
    """

    SCHEMA = PrepareExplanationDataSchema

    # Exactly the keys ``execute`` reads, and no more. ``dataset_id`` is
    # deliberately absent: the unit does not name it anywhere, and every key
    # listed here is demanded unconditionally by ``__call__``, so declaring an
    # unused one would reject any upstream that publishes a dataset without an
    # id — ``BuildManualInputUnit``, for one.
    REQUIRES = ("dataset", "model", "split_indexes")
    PROVIDES = ("data_x", "data_y", "task")
    # Supplied by the job only when the session declared preprocessing steps;
    # absent, there is nothing to apply. A path rather than the unpickled
    # object so a graph node can supply it like any other artifact location.
    RUNTIME_PARAMS = ("preprocessing_artifacts_path",)

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
            raise JobError(
                (f"Unable to find Task with name {task_name} in registry"),
            ) from e

        self._task = task
        return task

    def validate(self, ctx: ExecutionContext) -> None:
        """Resolve the task before anything observable happens.

        The orchestrator calls this outside the block that wraps preparation
        failures, which is what keeps a missing task reported as a registry
        problem instead of a generic "cannot prepare" message.
        """
        self._resolve_task()

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_dataset import (
            select_columns,
            split_dataset,
        )

        task = self._resolve_task()

        loaded_dataset = ctx.require("dataset")
        trained_model = ctx.require("model")
        splits = ctx.require("split_indexes")
        input_columns = self.config["input_columns"]
        output_columns = self.config["output_columns"]

        train_idx = splits["train_indexes"]
        test_idx = splits["test_indexes"]
        val_idx = splits["val_indexes"]

        artifacts_path = self.config.get("preprocessing_artifacts_path")
        if artifacts_path is not None:
            from DashAI.back.preprocessing.session_preprocessor import (
                transform_by_split,
            )

            # Split first, transform each part after: the run's indexes stay
            # valid even if a step removes rows (NanRemover), and no
            # resampled rows get in.
            preprocessor = load_persisted_preprocessor(artifacts_path)
            loaded_dataset, train_idx, test_idx, val_idx = transform_by_split(
                preprocessor, loaded_dataset, train_idx, test_idx, val_idx
            )

        loaded_dataset = split_dataset(
            loaded_dataset,
            train_indexes=train_idx,
            test_indexes=test_idx,
            val_indexes=val_idx,
        )

        prepared_dataset = task.prepare_for_task(
            dataset=loaded_dataset,
            input_columns=input_columns,
            output_columns=output_columns,
        )
        data = select_columns(prepared_dataset, input_columns, output_columns)

        data_x = split_dataset(
            data[0],
            train_indexes=train_idx,
            test_indexes=test_idx,
            val_indexes=val_idx,
        )
        data_y = split_dataset(
            data[1],
            train_indexes=train_idx,
            test_indexes=test_idx,
            val_indexes=val_idx,
        )
        # Inputs stay unprepared (see the class docstring); targets are encoded
        # because explainers compare them against the model's class indexes.
        for split_name in data_y:
            data_y[split_name] = trained_model.prepare_output(
                data_y[split_name], is_fit=False
            )

        ctx.put("data_x", data_x)
        ctx.put("data_y", data_y)
        ctx.put("task", task)
