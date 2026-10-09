"""Unit that fits a converter and transforms one dataset with it."""

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


class ApplyConverterSchema(BaseSchema):
    converter: converter_field()  # type: ignore
    scope: scope_field()  # type: ignore
    target: target_field()  # type: ignore


class ApplyConverterUnit(BaseUnit, ConverterScopeMixin):
    """Fit one converter on the scoped data and transform the same dataset.

    The single-dataset case, which is what applying a converter to a notebook
    means. Equivalent to :class:`FitConverterUnit` followed by
    :class:`TransformDatasetUnit` on the same dataset, kept as one unit for two
    reasons: it is the common case, and when there is no row scope it hands
    ``transform`` the very object ``fit`` saw, which some converters rely on to
    skip recomputing (see below).

    Use the split pair instead whenever the converter has to be learned from one
    dataset and applied to another — fit on train, transform on test.

    Reads ``dataset`` and writes ``dataset``: the same key on both sides, so any
    number of these can be chained in one context, each one seeing what the
    previous one produced.

    That is also why nothing about column identity ever crosses the context
    boundary. The scope is expressed as 1-based column and row indexes, and
    those indexes are resolved against ``dataset.column_names`` read at the top
    of ``execute`` — the dataset as it is *right now*. A converter that renames,
    drops or adds columns changes what index 3 means, so a resolved column list
    published to the context would be stale for the very next converter.
    """

    SCHEMA = ApplyConverterSchema

    REQUIRES = ("dataset",)
    PROVIDES = ("dataset", "fitted_converter")

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
        loaded_dataset: "DashAIDataset" = ctx.require("dataset")
        converter_name = self._converter_name

        converter_constructor = self._resolve_converter()
        converter_instance = converter_constructor(
            **(self.config["converter"].get("params") or {})
        )

        self._check_target_bounds(loaded_dataset)
        (
            scope_column_names,
            scope_rows_indexes,
            target_column_name,
        ) = self._resolve_scope(loaded_dataset)

        log.info(f"Applying converter: {converter_name}")

        x_dataset_fit, y_dataset_fit = self._slice_for_fit(
            loaded_dataset,
            scope_column_names,
            scope_rows_indexes,
            target_column_name,
        )

        converter_instance = self._fit(
            converter_instance, x_dataset_fit, y_dataset_fit, converter_name
        )

        if scope_rows_indexes:
            x_full_transform, y_full_transform = self._slice_for_transform(
                loaded_dataset, scope_column_names, target_column_name
            )
        else:
            # Deliberately the *same objects* as the ones passed to fit, not
            # equal ones: converters such as TypeCast key a cache off the
            # identity of the dataset they were fitted on and skip recomputing
            # when transform receives it again. Without a row scope the fit
            # slice already covers every row, so reusing it is also correct.
            x_full_transform, y_full_transform = x_dataset_fit, y_dataset_fit

        transformed_dataset = self._transform(
            converter_instance, x_full_transform, y_full_transform, converter_name
        )

        ctx.put(
            "dataset",
            self._merge_transformed(
                converter_instance,
                loaded_dataset,
                transformed_dataset,
                scope_column_names,
            ),
        )
        ctx.put("fitted_converter", converter_instance)
