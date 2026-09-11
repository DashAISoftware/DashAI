"""Unit that fits a converter on a dataset without transforming anything."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.converter_scope import (
    ConverterScopeMixin,
    converter_field,
    scope_field,
    target_field,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

log = logging.getLogger(__name__)


class FitConverterSchema(BaseSchema):
    converter: converter_field()  # type: ignore
    scope: scope_field()  # type: ignore
    target: target_field()  # type: ignore


class FitConverterUnit(BaseUnit, ConverterScopeMixin):
    """Fit a converter on the dataset in the context and publish it fitted.

    Splits the "fit" half out of :class:`ApplyConverterUnit` so a converter can
    be learned from one dataset and applied to another. That is the standard
    train/test discipline: a scaler, an encoder or an imputer must learn its
    statistics from the training data only, and then be applied unchanged to the
    test data — refitting on test would leak information into the evaluation.

    The dataset is left untouched: this unit produces a fitted converter, not
    data. Pair it with :class:`TransformDatasetUnit`, once per dataset the
    fitted converter has to be applied to.
    """

    SCHEMA = FitConverterSchema

    REQUIRES = ("dataset",)
    PROVIDES = ("fitted_converter",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        # Memoized on the instance, never in the context: two units of this
        # class can live in the same context and they are different converters.
        self._converter_class = None

    @property
    def _converter_name(self) -> str:
        return self.config["converter"]["component"]

    def _resolve_converter(self):
        """Look the converter class up in the registry, once per instance."""
        if self._converter_class is not None:
            return self._converter_class

        from kink import di

        component_registry = di["component_registry"]
        converter_name = self._converter_name

        try:
            self._converter_class = component_registry[converter_name]["class"]
        except KeyError as e:
            log.exception(e)
            raise JobError(f"Error importing converter {converter_name}: {e}") from e

        return self._converter_class

    def validate(self, ctx: ExecutionContext) -> None:
        """Reject an out-of-bounds target before any work is done."""
        self._check_target_bounds(ctx.require("dataset"))

    def execute(self, ctx: ExecutionContext) -> None:
        dataset: "DashAIDataset" = ctx.require("dataset")
        converter_name = self._converter_name

        converter_constructor = self._resolve_converter()
        converter_instance = converter_constructor(
            **(self.config["converter"].get("params") or {})
        )

        self._check_target_bounds(dataset)
        (
            scope_column_names,
            scope_rows_indexes,
            target_column_name,
        ) = self._resolve_scope(dataset)

        log.info(f"Fitting converter: {converter_name}")

        x_dataset, y_dataset = self._slice_for_fit(
            dataset,
            scope_column_names,
            scope_rows_indexes,
            target_column_name,
        )

        fitted = self._fit(converter_instance, x_dataset, y_dataset, converter_name)

        ctx.put("fitted_converter", fitted)
