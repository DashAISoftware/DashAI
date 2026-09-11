"""Unit that transforms a dataset with an already fitted converter."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.converter_scope import (
    ConverterScopeMixin,
    scope_field,
    target_field,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

log = logging.getLogger(__name__)


class TransformDatasetSchema(BaseSchema):
    scope: scope_field()  # type: ignore
    target: target_field()  # type: ignore


class TransformDatasetUnit(BaseUnit, ConverterScopeMixin):
    """Apply an already fitted converter to the dataset in the context.

    Takes no converter configuration: the converter arrives fitted through the
    context, from :class:`FitConverterUnit` or :class:`ApplyConverterUnit`. That
    is what makes "fit on train, apply to test" possible without refitting —
    run this once per dataset, and the converter keeps the state it learned.

    It does carry its own ``scope``, on purpose: the scope is a list of 1-based
    indexes, and they are resolved against **this** unit's dataset. Reusing the
    column names resolved during fit would break the moment the two datasets
    order their columns differently, and would carry stale column identity
    across the context boundary.
    """

    SCHEMA = TransformDatasetSchema

    REQUIRES = ("dataset", "fitted_converter")
    PROVIDES = ("dataset",)

    def validate(self, ctx: ExecutionContext) -> None:
        """Reject an out-of-bounds target before any work is done."""
        self._check_target_bounds(ctx.require("dataset"))

    def execute(self, ctx: ExecutionContext) -> None:
        dataset: "DashAIDataset" = ctx.require("dataset")
        converter_instance = ctx.require("fitted_converter")
        converter_name = type(converter_instance).__name__

        self._check_target_bounds(dataset)
        (
            scope_column_names,
            _scope_rows_indexes,
            target_column_name,
        ) = self._resolve_scope(dataset)

        log.info(f"Transforming with fitted converter: {converter_name}")

        x_dataset, y_dataset = self._slice_for_transform(
            dataset,
            scope_column_names,
            target_column_name,
        )

        transformed_dataset = self._transform(
            converter_instance, x_dataset, y_dataset, converter_name
        )

        ctx.put(
            "dataset",
            self._merge_transformed(
                converter_instance,
                dataset,
                transformed_dataset,
                scope_column_names,
            ),
        )
