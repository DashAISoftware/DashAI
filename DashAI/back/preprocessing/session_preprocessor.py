"""Fits and applies a ConverterSequence against dataset partitions.

SessionPreprocessor is fit once per session (per fold for Cross-Validation,
once for Holdout) by PreprocessingJob, then persisted so training,
prediction and explanation can reuse the exact fit without ever re-fitting
on new data (see load_final_preprocessor at the bottom of this module).
"""

import os
import pickle
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from DashAI.back.converters.dataset_columns import (
    rebuild_dataset_with_transformed_columns,
)
from DashAI.back.preprocessing.column_ref import ConverterSequence, resolve_refs

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SessionPreprocessor:
    """Fits and applies converters from a ConverterSequence.

    Each step's scope may reference raw dataset columns or the output group
    of an earlier step. Fitting always uses only the "train" entry of
    whatever split dict is passed in, so no step ever sees validation or
    test rows during fit.
    """

    def __init__(self, sequence: ConverterSequence, component_registry: Any):
        self.sequence = sequence
        self.component_registry = component_registry
        self.fitted_converters: List[Any] = []
        self.resolved_columns: Dict[int, List[str]] = {}

    def _instantiate(self, step) -> Any:
        converter_class = self.component_registry[step.converter]["class"]
        return converter_class(**step.params)

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

        for index, step in enumerate(self.sequence.steps):
            scope_names = resolve_refs(step.scope, self.resolved_columns)
            converter = self._instantiate(step)

            train_scope = current["train"].select_columns(scope_names)
            converter = converter.fit(train_scope)

            train_transformed = converter.transform(train_scope)
            transformed_by_split = {"train": train_transformed}
            for split_name, dataset in current.items():
                if split_name == "train":
                    continue
                transformed_by_split[split_name] = self._transform_split(
                    converter, dataset, scope_names, train_transformed
                )

            # A converter that only rewrites its scope columns in place (e.g. a
            # scaler: "age" in, scaled "age" out) has no other way to expose
            # its result, so the scope names ARE the group. But a converter
            # like Bag-of-Words additionally keeps its scope column verbatim
            # alongside brand-new derived columns (see BagOfWordsConverter.
            # transform's docstring: "the source text column is preserved
            # unchanged") — for those, the untouched scope column is a
            # passthrough, not this step's own output, so it must not leak
            # into the group a later step or the wizard's input selection can
            # reference (it would still carry the pre-conversion dtype, e.g.
            # Text, which is never valid as a resolved input column).
            new_columns = [
                name
                for name in train_transformed.column_names
                if name not in scope_names
            ]
            self.resolved_columns[index] = (
                new_columns if new_columns else list(train_transformed.column_names)
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
                self.sequence.steps[index].scope, self.resolved_columns
            )

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
        """Convenience wrapper for a single dataset (predict/explain use)."""
        return self.transform_only({"train": dataset})["train"]


def load_final_preprocessor(model_session: Any) -> "SessionPreprocessor":
    """Load the SessionPreprocessor fitted on the session's full training pool.

    Used by prediction and explanation, which must transform new raw data
    the exact same way the model's training data was transformed, without
    ever re-fitting on that new data.
    """
    path = os.path.join(model_session.preprocessing_artifacts_path, "final.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)
