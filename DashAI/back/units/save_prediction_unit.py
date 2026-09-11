"""Unit that stores a prediction alongside the data it was made on."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
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

        # Store num of rows, columns, and column names
        dataset_with_prediction.compute_base_metadata()

        save_dataset(
            dataset_with_prediction,
            str(full_path / "dataset"),
            filtered_schema,
        )

        ctx.put_ref("results_path", str(full_path))
