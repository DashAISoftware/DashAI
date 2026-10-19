"""Unit that renames columns and casts them to their declared types."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class ApplyDatasetSchemaSchema(BaseSchema):
    column_renames: schema_field(
        none_type(dict),
        placeholder=None,
        description=MultilingualString(
            en="Mapping of current column name to new name, applied before the "
            "types are cast. Columns not mentioned keep their name. The "
            "resulting names have to stay unique.",
            es="Mapa de nombre de columna actual a nombre nuevo, aplicado antes "
            "de convertir los tipos. Las columnas no mencionadas conservan su "
            "nombre. Los nombres resultantes tienen que seguir siendo únicos.",
            pt="Mapa de nome de coluna atual para nome novo, aplicado antes de "
            "converter os tipos. As colunas não mencionadas mantêm o seu nome. "
            "Os nomes resultantes têm de continuar únicos.",
            de="Zuordnung von aktuellem zu neuem Spaltennamen, angewendet vor "
            "der Typumwandlung. Nicht genannte Spalten behalten ihren Namen. "
            "Die resultierenden Namen müssen eindeutig bleiben.",
            zh="当前列名到新列名的映射，在类型转换前应用。未提及的列保留原名。"
            "结果列名必须保持唯一。",
        ),
        alias=MultilingualString(
            en="Column renames",
            es="Renombres de columnas",
            pt="Renomeações de colunas",
            de="Spaltenumbenennungen",
            zh="列重命名",
        ),
    )  # type: ignore


class ApplyDatasetSchemaUnit(BaseUnit):
    """Rename the dataset's columns and cast them to their declared types.

    Takes the type declaration from the context (``inferred_types``) rather than
    from its own configuration, so a single path feeds it whether the types were
    inferred upstream or handed in by whoever set up the run. Renaming and
    casting are one unit because a rename has to carry the declared types with
    it: the type declared for ``Species`` has to end up on ``Variety``, not be
    re-inferred from the data.

    ``validate`` rejects a declaration that names columns the dataset does not
    have. Without that check the mismatch is silent — the underlying transform
    passes unknown columns through untouched — so a stale declaration would
    quietly leave columns with inferred types instead of the requested ones.

    Note the deliberate asymmetry: the unit does **not** republish a renamed
    ``inferred_types``. After a rename that key describes column names that no
    longer exist, and republishing it would invite a second consumer to trust a
    declaration that no longer matches the dataset. Whoever needs types after
    this unit reads them off the dataset.
    """

    SCHEMA = ApplyDatasetSchemaSchema

    REQUIRES = ("dataset", "inferred_types")
    PROVIDES = ("dataset",)

    def validate(self, ctx: ExecutionContext) -> None:
        dataset = ctx.require("dataset")
        schema = ctx.require("inferred_types")

        unknown = sorted(set(schema) - set(dataset.column_names))
        if unknown:
            raise JobError(
                f"The declared types name columns the dataset does not have: {unknown}"
            )

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_dataset import (
            transform_dataset_with_schema,
        )

        dataset = ctx.require("dataset")
        schema = ctx.require("inferred_types")
        renames = self.config.get("column_renames")

        if renames:
            dataset, schema = _rename_columns(dataset, schema, renames)

        ctx.put("dataset", transform_dataset_with_schema(dataset, schema))


def _rename_columns(dataset, schema: dict, renames: dict):
    """Return the dataset with renamed columns and the schema remapped to match.

    A plain helper: it takes and returns values and never touches the context, so
    the unit's declared contract cannot hide inside it.
    """
    original_names = dataset.arrow_table.schema.names
    new_names = [renames.get(column, column) for column in original_names]

    if len(new_names) != len(set(new_names)):
        duplicate_names = set()
        seen = set()
        for name in new_names:
            if name in seen:
                duplicate_names.add(name)
            else:
                seen.add(name)
        raise JobError(
            "Invalid column_renames: resulting column names contain duplicates: "
            f"{sorted(duplicate_names)}"
        )

    arrow_table = dataset.arrow_table.rename_columns(new_names)
    renamed = dataset.__class__(
        arrow_table,
        splits=dataset.splits,
        types=dataset.types,
    )
    remapped_schema = {renames.get(column, column): schema[column] for column in schema}
    return renamed, remapped_schema
