"""Unit that stores a prediction alongside the data it was made on."""

import logging

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

log = logging.getLogger(__name__)


def _columns_field(alias: MultilingualString, description: MultilingualString):
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=description,
        alias=alias,
    )


class SavePredictionSchema(BaseSchema):
    task_name: schema_field(
        string_field(),
        placeholder="TabularClassificationTask",
        description=MultilingualString(
            en="Name of the task the model was trained for. It decides the "
            "declared type of the predicted column: a regression predicts "
            "continuous values whatever type its target was trained as.",
            es="Nombre de la tarea para la que se entrenó el modelo. Decide el "
            "tipo declarado de la columna predicha: una regresión predice "
            "valores continuos sin importar el tipo con que se entrenó su "
            "objetivo.",
            pt="Nome da tarefa para a qual o modelo foi treinado. Decide o tipo "
            "declarado da coluna prevista: uma regressão prevê valores "
            "contínuos seja qual for o tipo com que o seu alvo foi treinado.",
            de="Name der Aufgabe, für die das Modell trainiert wurde. Sie "
            "bestimmt den deklarierten Typ der vorhergesagten Spalte: eine "
            "Regression sagt stetige Werte voraus, gleich mit welchem Typ ihr "
            "Ziel trainiert wurde.",
            zh="模型所训练任务的名称。它决定预测列的声明类型：回归预测连续值，"
            "无论其目标以何种类型训练。",
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
            en="Names of the model input columns. Together with the output "
            "column they decide which declared types are kept in the schema "
            "written next to the result.",
            es="Nombres de las columnas de entrada del modelo. Junto con la "
            "columna de salida deciden qué tipos declarados se conservan en el "
            "esquema que se escribe junto al resultado.",
            pt="Nomes das colunas de entrada do modelo. Juntamente com a coluna "
            "de saída decidem que tipos declarados são mantidos no esquema "
            "escrito junto ao resultado.",
            de="Namen der Modelleingabespalten. Zusammen mit der Ausgabespalte "
            "bestimmen sie, welche deklarierten Typen im Schema neben dem "
            "Ergebnis erhalten bleiben.",
            zh="模型输入列的列名。它们与输出列共同决定结果旁写入的模式中保留哪些声明类型。",
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
            en="Names of the predicted columns. Only the first one is used: it "
            "names the column the predictions are written to.",
            es="Nombres de las columnas predichas. Solo se usa la primera: da "
            "nombre a la columna donde se escriben las predicciones.",
            pt="Nomes das colunas previstas. Apenas a primeira é usada: dá nome "
            "à coluna onde as previsões são escritas.",
            de="Namen der vorhergesagten Spalten. Nur die erste wird verwendet: "
            "sie benennt die Spalte für die Vorhersagen.",
            zh="预测列的列名。仅使用第一个：它命名写入预测结果的列。",
        ),
    )  # type: ignore


class SavePredictionUnit(BaseUnit):
    """Write the predicted column next to the data it was predicted from.

    The destination is a fresh folder under the datasets directory, named by a
    generated identifier: a prediction has no natural key to overwrite, so
    every run gets its own and no result can clobber another's.

    The columns to keep are resolved against the dataset the context holds
    right now, at the top of this method. Publishing a column list earlier
    would go stale the moment anything upstream renamed, added or dropped a
    column.

    The task is configuration, the same way ``PredictUnit`` receives it, and
    it is consulted for one thing: a regression predicts continuous values
    whatever type its target was trained as, so the predicted column is
    declared as a float rather than inheriting the training dataset's type.
    Inheriting it is not harmless: an integer-typed target makes the save cast
    ``1.5`` to ``int64``, and Arrow refuses the truncation.
    """

    SCHEMA = SavePredictionSchema

    REQUIRES = ("dataset", "y_pred", "train_dataset_types")
    PROVIDES = ("results_path",)

    def execute(self, ctx: ExecutionContext) -> None:
        import uuid
        from pathlib import Path

        from kink import di

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            save_dataset,
            to_dashai_dataset,
        )

        config = di["config"]

        dataset = ctx.require("dataset")
        y_pred = ctx.require("y_pred")
        train_dataset_types = ctx.require("train_dataset_types")

        input_columns = self.config["input_columns"]
        output_col = self.config["output_columns"][0]

        path = str(Path(f"{config['DATASETS_PATH']}/predictions/"))
        folder_name = str(uuid.uuid4())
        full_path = Path(path) / folder_name
        full_path.mkdir(parents=True, exist_ok=True)

        base_columns = [col for col in dataset.column_names if col != output_col]
        output_dataset = dataset.select_columns(base_columns)
        dataset_with_prediction = to_dashai_dataset(
            output_dataset.add_column(output_col, y_pred)
        )

        # Only the columns the model session declares carry a type; anything
        # the input dataset happened to bring along is left untyped.
        filtered_schema = {
            name: kind
            for name, kind in train_dataset_types.items()
            if name in input_columns + self.config["output_columns"]
        }

        # Regression models predict continuous values regardless of the
        # training target's original dtype (a target column that happened to
        # hold only integer-looking values, say), so the output column's saved
        # schema must reflect that instead of inheriting the training
        # dataset's type.
        if self._predicts_continuous_values():
            filtered_schema[output_col] = {"type": "Float", "dtype": "float64"}

        # Store num of rows, columns, and column names
        dataset_with_prediction.compute_base_metadata()

        save_dataset(
            dataset_with_prediction,
            str(full_path / "dataset"),
            filtered_schema,
        )

        ctx.put_ref("results_path", str(full_path))

    def _predicts_continuous_values(self) -> bool:
        """Whether the configured task is a regression, by its class.

        Resolved from the registry by name rather than instantiated: nothing
        here calls the task, so its class is all that is needed, and the check
        is the same subclass test ``isinstance`` would make on an instance.
        """
        from kink import di

        from DashAI.back.tasks.regression_task import RegressionTask

        task_name = self.config["task_name"]
        try:
            task_class = di["component_registry"][task_name]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(f"Task {task_name} not found in the registry") from e

        return issubclass(task_class, RegressionTask)
