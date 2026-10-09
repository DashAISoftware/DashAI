"""Fits and applies a ConverterSequence against dataset partitions.

SessionPreprocessor is fit once per session (per fold for Cross-Validation,
once for Holdout) by PreprocessingJob, then persisted so training,
prediction and explanation can reuse the exact fit without ever re-fitting
on new data (see load_final_preprocessor at the bottom of this module).
"""

import os
import pickle
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from DashAI.back.converters.dataset_columns import (
    plan_new_column_names,
    rebuild_dataset_with_transformed_columns,
)
from DashAI.back.preprocessing.column_ref import ConverterSequence, resolve_refs

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def _row_rule(converter: Any) -> Optional[str]:
    """Where a row-changing converter runs in a session, or None.

    "train": only on the training split (resampling). "splits": on every
    split, never on prediction inputs (row removal). None for converters
    that keep their rows, or row-changing ones sessions do not support.
    """
    converter_class = type(converter)
    if not converter_class.CHANGES_ROW_COUNT:
        return None
    rule = getattr(converter_class, "ROWS_APPLY_TO", None)
    return rule if rule in ("train", "splits") else None


class SessionPreprocessor:
    """Fits and applies converters from a ConverterSequence.

    Each step's scope may reference raw dataset columns or the output group
    of an earlier step. Fitting always uses only the "train" entry of
    whatever split dict is passed in, so no step ever sees validation or
    test rows during fit.

    Supervised converters (e.g. feature selectors) are fit with the
    `target_columns` of the train split as `y`. The target is never part of
    a step's scope, so no converter ever transforms it.
    """

    def __init__(
        self,
        sequence: ConverterSequence,
        component_registry: Any,
        target_columns: Optional[List[str]] = None,
    ):
        self.sequence = sequence
        self.component_registry = component_registry
        self.target_columns = list(target_columns or [])
        self.fitted_converters: List[Any] = []
        self.resolved_columns: Dict[int, List[str]] = {}
        self.resolved_slots: Dict[int, Dict[str, List[str]]] = {}

    def _instantiate(self, step) -> Any:
        converter_class = self.component_registry[step.converter]["class"]
        return converter_class(**step.params)

    @staticmethod
    def _classify_by_type(
        converter: Any, column_names: List[str]
    ) -> Dict[str, List[str]]:
        """Group a step's real output columns by their real, per-column type.

        Calls the now-fitted converter's own get_output_type(column_name) —
        already implemented by every converter, and already accurate once
        fitted (e.g. SimpleImputer's preserves the input column's own type
        for "most_frequent"/"constant"). Most converters produce one
        homogeneous type, so this is a single slot; a converter whose scope
        mixed column types (e.g. SimpleImputer imputing a categorical and a
        numeric column together) naturally splits into one slot per type,
        with no converter-specific code needed here or in the converter
        itself.
        """
        slots: Dict[str, List[str]] = {}
        for name in column_names:
            output_type = converter.get_output_type(name)
            type_name = (
                output_type.display_name()
                if output_type is not None and hasattr(output_type, "display_name")
                else "unknown"
            )
            slots.setdefault(type_name, []).append(name)
        return slots

    def _fit(self, converter: Any, train: "DashAIDataset", train_scope) -> Any:
        """Fit a step's converter, passing the target to supervised ones."""
        # A preprocessor pickled before target_columns existed has no such
        # attribute; it is only unpickled to transform, never to fit again.
        target_columns = getattr(self, "target_columns", None)
        if type(converter).SUPERVISED and target_columns:
            return converter.fit(train_scope, train.select_columns(target_columns))
        return converter.fit(train_scope)

    def _record_group(
        self,
        index: int,
        converter: Any,
        train: "DashAIDataset",
        scope_names: List[str],
        output_names: List[str],
    ) -> None:
        """Record which real columns a step produced, and their slots.

        A converter that only rewrites its scope columns in place (e.g. a
        scaler: "age" in, scaled "age" out) has no other way to expose its
        result, so the scope names ARE the group. A converter that adds new
        columns (e.g. Bag-of-Words, which also keeps its scope column
        verbatim) only exposes the new ones: a passthrough scope column is
        not this step's output, and would still carry its pre-conversion
        type (e.g. Text), which is never valid as a resolved input column.

        New columns are recorded under the final name they get in the
        dataset: one whose name is already taken is renamed by
        rebuild_dataset_with_transformed_columns (e.g. "derived_1"). Slots
        are classified with the names the converter itself produced, since
        that is what its get_output_type knows.
        """
        new_columns = [name for name in output_names if name not in scope_names]
        if not new_columns:
            self.resolved_columns[index] = list(output_names)
            self.resolved_slots[index] = self._classify_by_type(
                converter, self.resolved_columns[index]
            )
            return

        removed = {name for name in scope_names if name not in output_names}
        final_names = plan_new_column_names(
            [name for name in train.column_names if name not in removed],
            new_columns,
        )
        self.resolved_columns[index] = [final_names[name] for name in new_columns]
        self.resolved_slots[index] = {
            type_name: [final_names[name] for name in names]
            for type_name, names in self._classify_by_type(
                converter, new_columns
            ).items()
        }

    def _apply_row_step(
        self,
        converter: Any,
        current: Dict[str, "DashAIDataset"],
        scope_names: List[str],
        rule: str,
        fit: bool,
    ) -> Dict[str, "DashAIDataset"]:
        """Apply a row-changing step to every split, following its rule.

        Every split keeps only the step's scope and, when present, the
        target, as the converter's own output does in notebooks, so all
        splits share the same columns. A prediction input ("predict") never
        loses or gains rows.

        - "train": the train split is resampled, fitting the converter on it
          every time (a resampler learns nothing to apply to other data);
          every other split keeps its rows.
        - "splits": every split but "predict" keeps only the rows the
          converter reports with ``rows_to_keep``, cut on the whole split so
          inputs and target stay aligned. The converter is fit once, on the
          train split, when ``fit`` is true.
        """
        name = type(converter).__name__
        target_columns = list(getattr(self, "target_columns", None) or [])
        if rule == "train" and len(target_columns) != 1:
            raise ValueError(
                f"{name} needs exactly one target column to resample, "
                f"got {len(target_columns)}."
            )
        if rule == "splits" and fit and "train" in current:
            converter.fit(current["train"].select_columns(scope_names))

        new_current = {}
        for split_name, dataset in current.items():
            has_target = bool(target_columns) and all(
                c in dataset.column_names for c in target_columns
            )
            keep = scope_names + (target_columns if has_target else [])
            if split_name == "predict" or (rule == "train" and split_name != "train"):
                new_current[split_name] = dataset.select_columns(keep)
                continue
            if rule == "train":
                if not has_target:
                    raise ValueError(
                        f"{name} needs the target column '{target_columns[0]}' "
                        "in the training split."
                    )
                scoped = dataset.select_columns(scope_names)
                target = dataset.select_columns(target_columns)
                converter.fit(scoped, target)
                new_current["train"] = converter.transform(scoped, target)
                continue
            positions = converter.rows_to_keep(dataset.select_columns(scope_names))
            if dataset.num_rows > 0 and not positions:
                raise ValueError(
                    f"{name} removed every row of the '{split_name}' split."
                )
            new_current[split_name] = dataset.select(positions).select_columns(keep)
        return new_current

    @staticmethod
    def _transform_split(converter, dataset, scope_names, train_transformed):
        """Transform one split's scoped columns, without crashing on 0 rows.

        A "test" (or similar) partition can legitimately have 0 rows — e.g.
        a session that reserved nothing for the final refit — and several
        sklearn transformers raise on an empty array. Since train_transformed
        (computed first) has the same columns any non-empty split would
        produce, an empty split reuses that shape with 0 rows instead of
        calling the converter at all.
        """
        scoped = dataset.select_columns(scope_names)
        if scoped.num_rows == 0 and train_transformed is not None:
            return train_transformed.select([])
        return converter.transform(scoped)

    def __getstate__(self):
        """Exclude component_registry from pickling.

        The registry is only needed to instantiate converters during
        fit_transform; a fitted preprocessor is persisted precisely so that
        step never runs again. The registry itself is not picklable (it
        holds RelationshipManager lambdas), so it must never travel with the
        pickled object.
        """
        state = self.__dict__.copy()
        state["component_registry"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def fit_transform(
        self, split: Dict[str, "DashAIDataset"]
    ) -> Tuple[Dict[str, "DashAIDataset"], Dict[int, List[str]]]:
        """Fit every step on split["train"] and transform every split present.

        Parameters
        ----------
        split : dict
            Whatever partitions are present (e.g. {"train", "validation"},
            {"train", "validation", "test"} or {"train", "test"}) are
            transformed, but only "train" is ever used to fit.

        Returns
        -------
        tuple
            (transformed_split, resolved_columns) where transformed_split
            has the same keys as split and resolved_columns maps each
            step's index to the concrete column names it produced.
        """
        current: Dict[str, "DashAIDataset"] = dict(split)
        self.fitted_converters = []
        self.resolved_columns = {}
        self.resolved_slots = {}

        for index, step in enumerate(self.sequence.steps):
            scope_names = resolve_refs(
                step.scope, self.resolved_columns, self.resolved_slots
            )
            converter = self._instantiate(step)

            rule = _row_rule(converter)
            if rule is not None:
                current = self._apply_row_step(
                    converter, current, scope_names, rule, fit=True
                )
                # The step's output columns are its scope columns; the target
                # that travels alongside them is not a column of its.
                self.resolved_columns[index] = list(scope_names)
                self.resolved_slots[index] = self._classify_by_type(
                    converter, scope_names
                )
                self.fitted_converters.append(converter)
                continue

            train_scope = current["train"].select_columns(scope_names)
            converter = self._fit(converter, current["train"], train_scope)

            train_transformed = converter.transform(train_scope)
            transformed_by_split = {"train": train_transformed}
            for split_name, dataset in current.items():
                if split_name == "train":
                    continue
                transformed_by_split[split_name] = self._transform_split(
                    converter, dataset, scope_names, train_transformed
                )

            self._record_group(
                index,
                converter,
                current["train"],
                scope_names,
                list(train_transformed.column_names),
            )

            new_current = {}
            for split_name, dataset in current.items():
                if type(converter).CHANGES_ROW_COUNT:
                    new_current[split_name] = transformed_by_split[split_name]
                else:
                    scope_indexes = [
                        dataset.column_names.index(name) for name in scope_names
                    ]
                    new_current[split_name] = rebuild_dataset_with_transformed_columns(
                        dataset,
                        transformed_by_split[split_name],
                        scope_names,
                        scope_indexes,
                    )
            current = new_current
            self.fitted_converters.append(converter)

        return current, self.resolved_columns

    def transform_only(
        self, split: Dict[str, "DashAIDataset"]
    ) -> Dict[str, "DashAIDataset"]:
        """Apply already-fitted converters to new data, without fitting.

        Used after unpickling a SessionPreprocessor that was fit earlier (by
        PreprocessingJob), to transform fold data at training time, or a
        prediction/explanation input.
        """
        current: Dict[str, "DashAIDataset"] = dict(split)
        for index, converter in enumerate(self.fitted_converters):
            scope_names = resolve_refs(
                self.sequence.steps[index].scope,
                self.resolved_columns,
                self.resolved_slots,
            )

            rule = _row_rule(converter)
            if rule is not None:
                current = self._apply_row_step(
                    converter, current, scope_names, rule, fit=False
                )
                continue

            train_transformed = None
            if "train" in current:
                train_transformed = converter.transform(
                    current["train"].select_columns(scope_names)
                )

            transformed_by_split = {}
            if train_transformed is not None:
                transformed_by_split["train"] = train_transformed
            for split_name, dataset in current.items():
                if split_name == "train":
                    continue
                transformed_by_split[split_name] = self._transform_split(
                    converter, dataset, scope_names, train_transformed
                )

            new_current = {}
            for split_name, dataset in current.items():
                transformed = transformed_by_split[split_name]
                if type(converter).CHANGES_ROW_COUNT:
                    new_current[split_name] = transformed
                else:
                    scope_indexes = [
                        dataset.column_names.index(name) for name in scope_names
                    ]
                    new_current[split_name] = rebuild_dataset_with_transformed_columns(
                        dataset, transformed, scope_names, scope_indexes
                    )
            current = new_current
        return current

    def transform_dataset(self, dataset: "DashAIDataset") -> "DashAIDataset":
        """Transform a single dataset (predict/explain use).

        Wrapped under its own "predict" key, never "train", so no step adds
        or removes rows of it: neither resampling nor row removal
        (NanRemover) touches prediction inputs.
        """
        return self.transform_only({"predict": dataset})["predict"]


def transform_by_split(
    preprocessor: "SessionPreprocessor",
    dataset: "DashAIDataset",
    train_indexes: List[int],
    test_indexes: List[int],
    val_indexes: List[int],
) -> Tuple["DashAIDataset", List[int], List[int], List[int]]:
    """Transform a dataset split by split, and reindex the splits.

    Used by explainers, which need the run's train/test/validation rows
    after preprocessing. Splitting first and transforming each part keeps
    the run's indexes valid even when a step removes rows (NanRemover), and
    the parts' keys are neither "train" nor "predict", so incomplete rows
    are removed and no synthetic (resampled) rows are added. An empty part
    is not transformed: it takes the transformed train part's columns with
    no rows.

    Parameters
    ----------
    preprocessor : SessionPreprocessor
        The fitted preprocessor of the run's session.
    dataset : DashAIDataset
        The raw dataset the run was trained on.
    train_indexes, test_indexes, val_indexes : list of int
        The run's split indexes over ``dataset``.

    Returns
    -------
    tuple
        (dataset, train_indexes, test_indexes, val_indexes): the transformed
        parts concatenated in train, test, validation order, and each
        part's positions in it.
    """
    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import (
        DashAIDataset,
        split_dataset,
    )

    parts = split_dataset(
        dataset,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )
    names = ["train", "test", "validation"]
    non_empty = {
        f"explain_{name}": parts[name] for name in names if parts[name].num_rows > 0
    }
    transformed = preprocessor.transform_only(non_empty)
    template = transformed["explain_train"]
    ordered = [
        transformed.get(f"explain_{name}", template.select([])) for name in names
    ]
    table = pa.concat_tables([part.arrow_table for part in ordered])
    merged = DashAIDataset(table, types=template.types)

    offsets, start = [], 0
    for part in ordered:
        offsets.append(list(range(start, start + part.num_rows)))
        start += part.num_rows
    return merged, offsets[0], offsets[1], offsets[2]


def load_final_preprocessor(model_session: Any) -> "SessionPreprocessor":
    """Load the SessionPreprocessor fitted on the session's full training pool.

    Used by prediction and explanation, which must transform new raw data
    the exact same way the model's training data was transformed, without
    ever re-fitting on that new data.
    """
    path = os.path.join(model_session.preprocessing_artifacts_path, "final.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)
