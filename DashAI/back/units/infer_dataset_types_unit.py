"""Unit that works out what type each column of a dataset holds."""

import logging

from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class InferDatasetTypesSchema(BaseSchema):
    method: schema_field(
        string_field(),
        placeholder="DashAIPtype",
        description=MultilingualString(
            en="Inference method used when the dataset does not already carry "
            "types of its own.",
            es="Método de inferencia que se usa cuando el conjunto de datos no "
            "trae tipos propios.",
            pt="Método de inferência usado quando o conjunto de dados não traz "
            "tipos próprios.",
            de="Inferenzmethode, die verwendet wird, wenn der Datensatz keine "
            "eigenen Typen mitbringt.",
            zh="当数据集本身未携带类型时使用的推断方法。",
        ),
        alias=MultilingualString(
            en="Inference method",
            es="Método de inferencia",
            pt="Método de inferência",
            de="Inferenzmethode",
            zh="推断方法",
        ),
    )  # type: ignore


class InferDatasetTypesUnit(BaseUnit):
    """Publish a type declaration for every column of the dataset.

    Prefers the types the dataset already carries: a dataloader that can read
    them from the source (a Parquet schema, a typed database column) knows better
    than any inference over the values, so re-inferring would throw that away.
    Only when there are none does it fall back to inferring from the data.

    Publishes the declaration as a plain reference rather than applying it, so
    the decision and the transformation stay separable — the same declaration can
    be shown to a user for review before anything is cast.

    Note the reference names columns, so it goes stale the moment something
    renames or drops one. It is meant to be consumed by the next step, not
    carried across a chain of transformations.
    """

    SCHEMA = InferDatasetTypesSchema

    REQUIRES = ("dataset",)
    PROVIDES = ("inferred_types",)

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.types.inf.type_inference import infer_types

        dataset = ctx.require("dataset")

        if dataset.types:
            schema = {
                column: dashai_type.to_string()
                for column, dashai_type in dataset.types.items()
            }
        else:
            schema = infer_types(
                dataset.to_pandas(),
                method=self.config.get("method", "DashAIPtype"),
            )

        ctx.put_ref("inferred_types", schema)
