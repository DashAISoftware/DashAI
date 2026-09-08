import os

import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler as SkStandardScaler

from DashAI.back.converters.execution import (
    apply_session_converters,
    fit_transform_on_partition,
    fitted_converters_path,
    load_fitted_converters,
    record_group_columns,
    save_fitted_converters,
    transform_for_prediction,
)
from DashAI.back.converters.imbalanced_learn.random_under_sampler_converter import (
    RandomUnderSamplerConverter,
)
from DashAI.back.converters.scikit_learn.bag_of_words import BagOfWordsConverter
from DashAI.back.converters.scikit_learn.binarizer import Binarizer
from DashAI.back.converters.scikit_learn.pca import PCA
from DashAI.back.converters.scikit_learn.select_k_best import SelectKBest
from DashAI.back.converters.scikit_learn.standard_scaler import StandardScaler
from DashAI.back.converters.scikit_learn.tf_idf import TFIDFConverter
from DashAI.back.converters.simple_converters.column_arithmetic import (
    ColumnArithmetic,
)
from DashAI.back.converters.simple_converters.column_concat import ColumnConcat
from DashAI.back.converters.simple_converters.nan_remover import NanRemover
from DashAI.back.converters.simple_converters.numeric_expansion import (
    NumericExpansion,
)
from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Float, Text


def _dataset(df: pd.DataFrame):
    return to_dashai_dataset(df)


def _typed_dataset(df: pd.DataFrame, types: dict):
    """Like `_dataset`, but embeds explicit DashAI types instead of leaving
    the dataset's type metadata empty. Needed for converters (e.g.
    `ColumnArithmetic`, `ColumnConcat`, `NumericExpansion`) that check
    `x.types.get(col)` themselves — most test converters don't, so
    `_dataset`'s untyped datasets pass for them, but not for these."""
    return to_dashai_dataset(df, types=types)


def _registry(*classes):
    """Minimal stand-in for ComponentRegistry: only supports `[name]["class"]`."""
    return {cls.__name__: {"class": cls} for cls in classes}


def _converter_config(name, params=None, columns=None, id="conv_0"):  # noqa: A002
    return {
        "id": id,
        "converter": name,
        "params": params or {},
        "columns": columns or [],
    }


def test_fit_uses_only_train_rows_not_test():
    """The scaler's learned mean/std must come from train alone, and the same
    fitted instance (not a re-fit) must be used to transform test."""
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1, 0, 1]}))
    # test has a very different distribution; if the scaler leaked into it,
    # the transformed values below would not match a train-only fit.
    x_test = _dataset(pd.DataFrame({"a": [100.0, 200.0]}))

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler")]

    new_x_train, new_y_train, x_others, fitted = fit_transform_on_partition(
        config, registry, x_train, y_train, x_others={"test": x_test}
    )

    expected = SkStandardScaler().fit(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]}))

    assert new_x_train.to_pandas()["a"].tolist() == pytest.approx(
        expected.transform(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})).ravel().tolist()
    )
    # test transformed using train's mean/std, not its own.
    assert x_others["test"].to_pandas()["a"].tolist() == pytest.approx(
        expected.transform(pd.DataFrame({"a": [100.0, 200.0]})).ravel().tolist()
    )
    # y is untouched by a non-sampler converter.
    assert new_y_train.to_pandas()["target"].tolist() == [0, 1, 0, 1]
    # the fitted StandardScaler instance is captured for prediction-time reuse.
    assert len(fitted) == 1
    assert fitted[0]["columns"] == ["a"]
    assert fitted[0]["instance"].transform(
        _dataset(pd.DataFrame({"a": [100.0, 200.0]}))
    ).to_pandas()["a"].tolist() == pytest.approx(
        expected.transform(pd.DataFrame({"a": [100.0, 200.0]})).ravel().tolist()
    )


def test_partial_column_scope_leaves_other_columns_untouched():
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1, 0]}))
    x_test = _dataset(pd.DataFrame({"a": [5.0], "b": [50.0]}))

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler", columns=["a"])]

    new_x_train, _, x_others, _ = fit_transform_on_partition(
        config, registry, x_train, y_train, x_others={"test": x_test}
    )

    assert new_x_train.to_pandas()["b"].tolist() == [10.0, 20.0, 30.0]
    assert x_others["test"].to_pandas()["b"].tolist() == [50.0]
    # column "a" did change (scaled).
    assert new_x_train.to_pandas()["a"].tolist() != [1.0, 2.0, 3.0]


def test_sampler_only_changes_train_not_test_or_validation():
    # 15 majority (class 0) + 5 minority (class 1) rows.
    df_x = pd.DataFrame({"a": list(range(20))})
    df_y = pd.DataFrame({"target": [0] * 15 + [1] * 5})
    x_train = _dataset(df_x)
    y_train = _dataset(df_y)
    x_validation = _dataset(pd.DataFrame({"a": [999.0]}))
    x_test = _dataset(pd.DataFrame({"a": [888.0]}))

    registry = _registry(RandomUnderSamplerConverter)
    config = [
        _converter_config(
            "RandomUnderSamplerConverter",
            params={"sampling_strategy": "auto", "random_state": 0},
        )
    ]

    new_x_train, new_y_train, x_others, fitted = fit_transform_on_partition(
        config,
        registry,
        x_train,
        y_train,
        x_others={"validation": x_validation, "test": x_test},
    )

    # Majority class down-sampled to match the minority class (5 and 5).
    assert len(new_x_train) == 10
    assert len(new_y_train) == 10
    # validation/test are completely unaffected by the resampling.
    assert x_others["validation"].to_pandas()["a"].tolist() == [999.0]
    assert x_others["test"].to_pandas()["a"].tolist() == [888.0]
    # samplers are never captured for prediction-time replay.
    assert fitted == []


def test_nan_remover_keeps_x_and_y_aligned_and_merged():
    """Regression test: NanRemover changes the row count (CHANGES_ROW_COUNT),
    so `fit_transform_on_partition` feeds it x_train/y_train and expects a
    combined dataset back to split apart again (same contract as samplers).
    NanRemover.transform used to ignore `y` entirely, so the output column
    was silently dropped and the follow-up split blew up with a KeyError."""
    x_train = _dataset(pd.DataFrame({"a": [1.0, None, 3.0, 4.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1, 0, 1]}))
    x_test = _dataset(pd.DataFrame({"a": [999.0]}))

    registry = _registry(NanRemover)
    config = [_converter_config("NanRemover")]

    new_x_train, new_y_train, x_others, fitted = fit_transform_on_partition(
        config, registry, x_train, y_train, x_others={"test": x_test}
    )

    # the row with a NaN in "a" is dropped from both x and y, in sync.
    assert new_x_train.to_pandas()["a"].tolist() == [1.0, 3.0, 4.0]
    assert new_y_train.to_pandas()["target"].tolist() == [0, 0, 1]
    # test is left untouched, like any other row-count-changing converter.
    assert x_others["test"].to_pandas()["a"].tolist() == [999.0]
    assert fitted == []


def test_empty_other_partition_is_skipped():
    """The CV 'full_dataset' fold has an empty test partition; it must not
    be transformed (there is nothing to transform, and no error raised)."""
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1, 0]}))
    empty_x = _dataset(pd.DataFrame({"a": []}))

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler")]

    _, _, x_others, _ = fit_transform_on_partition(
        config, registry, x_train, y_train, x_others={"test": empty_x}
    )
    assert len(x_others["test"]) == 0


def test_fit_failure_raises_joberror_with_context():
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1]}))

    registry = _registry(PCA)
    # n_components > number of features/rows available: sklearn raises.
    config = [_converter_config("PCA", params={"n_components": 5})]

    with pytest.raises(JobError, match="PCA"):
        fit_transform_on_partition(
            config, registry, x_train, y_train, x_others={}, partition_label="fold_0"
        )


def test_non_supervised_converter_scoped_to_output_column_raises_clear_error():
    """A non-supervised converter (e.g. LabelEncoder) scoped to the
    session's own output column can never fit: `y_train` already holds the
    target, separated out of `x_train` before any converter runs. This
    must raise a clear, specific error instead of a raw pyarrow KeyError."""
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0]}))
    y_train = _dataset(pd.DataFrame({"target": ["yes", "no"]}))

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler", columns=["target"])]

    with pytest.raises(JobError, match="output column"):
        fit_transform_on_partition(
            config, registry, x_train, y_train, x_others={}, partition_label="fold_0"
        )


def test_supervised_converter_uses_local_target_column_from_x_when_set():
    """When a converter's config carries `target_column` (the per-converter
    local target, used before the session has a real output column), a
    SUPERVISED converter must fit against that column pulled from x_train —
    not against y_train, which is empty in this scenario (no session output
    column chosen yet)."""
    x_train = _dataset(
        pd.DataFrame(
            {
                "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "b": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
                "label": [0, 0, 0, 1, 1, 1],
            }
        )
    )
    y_train = to_dashai_dataset(pd.DataFrame(index=range(6)))
    assert y_train.column_names == []

    registry = _registry(SelectKBest)
    config = [_converter_config("SelectKBest", params={"k": 1}, columns=["a", "b"])]
    config[0]["target_column"] = "label"

    new_x_train, new_y_train, _x_others, fitted = fit_transform_on_partition(
        config, registry, x_train, y_train, x_others={}
    )

    # SelectKBest(k=1) drops one of "a"/"b"; "label" was never in `columns`
    # (the transform scope) so it must survive untouched in x_train.
    assert "label" in new_x_train.column_names
    assert len(fitted) == 1
    assert new_y_train.column_names == []


def test_apply_session_converters_holdout_shape():
    x = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})),
        "validation": _dataset(pd.DataFrame({"a": [5.0]})),
        "test": _dataset(pd.DataFrame({"a": [6.0]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0, 1]})),
        "validation": _dataset(pd.DataFrame({"target": [0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler")]

    new_x, new_y, fitted, _group_registry = apply_session_converters(
        x, y, config, registry
    )

    assert set(new_x.keys()) == {"train", "validation", "test"}
    assert len(new_x["train"]) == 4
    assert len(new_x["validation"]) == 1
    assert len(new_y["validation"]) == 1
    # holdout has a single train partition, so its fit is "the" final fit.
    assert len(fitted) == 1


def test_cv_non_supervised_converter_fits_once_and_matches_across_folds():
    """A non-supervised, non-row-changing converter (StandardScaler here,
    standing in for anything data-dependent like a text vectorizer) must
    produce IDENTICAL fitted parameters across every fold — because it's
    fit once on full_dataset and reused via transform(), never refit per
    fold. Different train subsets would normally give different mean/std;
    identical values across folds is the signal the fix is working."""
    fold_0 = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0]})),
        "test": _dataset(pd.DataFrame({"a": [10.0]})),
    }
    fold_1 = {
        "train": _dataset(pd.DataFrame({"a": [100.0, 200.0, 300.0]})),
        "test": _dataset(pd.DataFrame({"a": [150.0]})),
    }
    full_dataset = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]})),
        "test": _dataset(pd.DataFrame({"a": []})),
    }
    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }
    y_fold_1 = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0, 0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, fold_1, full_dataset]
    y = [y_fold_0, y_fold_1, y_full_dataset]

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler")]

    new_x, _, fitted, _group_registry = apply_session_converters(x, y, config, registry)

    # Fit only on full_dataset's train (all 6 rows) — same expected
    # transform everywhere, including fold_0/fold_1's own test partitions.
    full_expected = SkStandardScaler().fit(
        pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]})
    )

    fold_0_transformed_test = new_x[0]["test"].to_pandas()["a"].tolist()
    fold_1_transformed_test = new_x[1]["test"].to_pandas()["a"].tolist()

    assert fold_0_transformed_test == pytest.approx(
        full_expected.transform(pd.DataFrame({"a": [10.0]})).ravel().tolist()
    )
    assert fold_1_transformed_test == pytest.approx(
        full_expected.transform(pd.DataFrame({"a": [150.0]})).ravel().tolist()
    )
    # fold_0's own train, transformed with the SAME (full_dataset-fitted)
    # scaler — NOT what an independent per-fold fit on [1,2,3] would give.
    fold_0_train_transformed = new_x[0]["train"].to_pandas()["a"].tolist()
    assert fold_0_train_transformed == pytest.approx(
        full_expected.transform(pd.DataFrame({"a": [1.0, 2.0, 3.0]})).ravel().tolist()
    )

    # full_dataset (last entry) fit on the whole dataset; its empty test
    # partition is left alone (no error, still empty).
    assert len(new_x[2]["test"]) == 0
    assert new_x[2]["train"].to_pandas()["a"].tolist() == pytest.approx(
        full_expected.transform(
            pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]})
        )
        .ravel()
        .tolist()
    )
    # the fitted converters returned are the full_dataset fold's fit.
    assert len(fitted) == 1
    assert fitted[0]["instance"].transform(
        _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]}))
    ).to_pandas()["a"].tolist() == pytest.approx(
        full_expected.transform(
            pd.DataFrame({"a": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]})
        )
        .ravel()
        .tolist()
    )


def test_cv_supervised_converter_still_fits_independently_per_fold():
    """Unchanged-behavior guard: a SUPERVISED converter (sampler here) must
    keep fitting independently per fold — this must NOT be swept into the
    fit-once path, since that would leak target information across folds."""
    df_x = pd.DataFrame({"a": list(range(20))})
    df_y = pd.DataFrame({"target": [0] * 15 + [1] * 5})
    fold_0 = {"train": _dataset(df_x), "test": _dataset(pd.DataFrame({"a": [999.0]}))}
    full_dataset = {"train": _dataset(df_x), "test": _dataset(pd.DataFrame({"a": []}))}
    y_fold_0 = {
        "train": _dataset(df_y),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }
    y_full_dataset = {
        "train": _dataset(df_y),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, full_dataset]
    y = [y_fold_0, y_full_dataset]

    registry = _registry(RandomUnderSamplerConverter)
    config = [
        _converter_config(
            "RandomUnderSamplerConverter",
            params={"sampling_strategy": "auto", "random_state": 0},
        )
    ]

    new_x, new_y, fitted, _group_registry = apply_session_converters(
        x, y, config, registry
    )

    # Both folds independently resampled the SAME 20-row input to 10 rows —
    # the real guard is that x_others (test) stayed untouched, same as
    # before this change (samplers never touch validation/test).
    assert len(new_x[0]["train"]) == 10
    assert len(new_x[1]["train"]) == 10
    assert new_x[0]["test"].to_pandas()["a"].tolist() == [999.0]
    assert fitted == []  # samplers are never kept for prediction-time replay


def test_cv_non_supervised_row_changing_converter_still_fits_per_fold():
    """A non-supervised converter that changes row count (NanRemover) is
    NOT swept into the fit-once path either — only fit_transform_on_partition's
    existing CHANGES_ROW_COUNT handling (train-only, x_others untouched)
    applies, same as it always has. NanRemover's own fit doesn't depend on
    row content (only column names/types), so per-fold independent fits
    already produce identical columns everywhere — no consistency problem
    to solve here in the first place."""
    fold_0 = {
        "train": _dataset(pd.DataFrame({"a": [1.0, None, 3.0]})),
        "test": _dataset(pd.DataFrame({"a": [10.0]})),
    }
    full_dataset = {
        "train": _dataset(pd.DataFrame({"a": [1.0, None, 3.0, 4.0, None]})),
        "test": _dataset(pd.DataFrame({"a": []})),
    }
    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, full_dataset]
    y = [y_fold_0, y_full_dataset]

    registry = _registry(NanRemover)
    config = [_converter_config("NanRemover")]

    new_x, new_y, _, _group_registry = apply_session_converters(x, y, config, registry)

    # fold_0's own 1 NaN row dropped from its own 3-row train -> 2 rows.
    assert len(new_x[0]["train"]) == 2
    # full_dataset's own 2 NaN rows dropped from its own 5-row train -> 3.
    assert len(new_x[1]["train"]) == 3
    # test partitions untouched, as CHANGES_ROW_COUNT converters always do.
    assert len(new_x[0]["test"]) == 1


def test_input_scope_resolves_group_from_earlier_converter_holdout():
    """converter_1 (ColumnArithmetic-like stand-in) adds a new column; converter_2's
    input_scope references converter_1's whole group by id, and must resolve to
    whatever real column(s) converter_1 actually produced."""
    df_x = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    x = {
        "train": _dataset(df_x),
        "test": _dataset(pd.DataFrame({"a": [4.0], "b": [40.0]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(StandardScaler)
    config = [
        {
            "id": "conv_0",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "column", "name": "a"}],
        },
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    # conv_0 only touched "a" (its own scope); conv_1's scope resolves to
    # exactly that same real column, "a", not the untouched "b".
    assert group_registry[("conv_0", 0)][0] == ["a"]
    assert "b" in new_x["train"].column_names
    assert len(fitted) == 2


def test_group_registry_excludes_untouched_original_for_prefix_appending_converter():
    """`Binarizer` (like `LabelEncoder`/`OrdinalEncoder`/`OneHotEncoder`,
    all sharing `EncodingConverter`) keeps its scope column untouched and
    appends a new `bin_<col>` column alongside it. Its group's real columns
    must be only the new `bin_<col>` column, never the untouched original —
    otherwise selecting both the group and the literal original column as
    separate atoms would silently resolve to the same real column twice."""
    df_x = pd.DataFrame({"study_hours": [1.0, 5.0, 9.0], "other": [1.0, 2.0, 3.0]})
    x = {
        "train": _dataset(df_x),
        "test": _dataset(pd.DataFrame({"study_hours": [4.0], "other": [4.0]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(Binarizer)
    config = [
        {
            "id": "conv_0",
            "converter": "Binarizer",
            "params": {"threshold": 0.0},
            "input_scope": [{"kind": "column", "name": "study_hours"}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    assert group_registry[("conv_0", 0)][0] == ["bin_study_hours"]
    assert "study_hours" in new_x["train"].column_names
    assert "bin_study_hours" in new_x["train"].column_names


def test_group_registry_excludes_untouched_original_for_bag_of_words():
    """`BagOfWordsConverter` keeps its scope text column untouched and
    appends one `bow_<token>` column per vocabulary term — its group's
    real columns must be only the `bow_*` columns, never the untouched
    original text column."""
    df_x = pd.DataFrame({"text": ["cat dog", "dog dog", "cat"], "other": [1, 2, 3]})
    x = {
        "train": _dataset(df_x),
        "test": _dataset(pd.DataFrame({"text": ["cat"], "other": [4]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(BagOfWordsConverter)
    config = [
        {
            "id": "conv_0",
            "converter": "BagOfWordsConverter",
            "params": {},
            "input_scope": [{"kind": "column", "name": "text"}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    group_columns = group_registry[("conv_0", 0)][0]
    assert "text" not in group_columns
    assert all(name.startswith("bow_") for name in group_columns)
    assert len(group_columns) > 0
    assert "text" in new_x["train"].column_names


def test_group_registry_excludes_untouched_original_for_tfidf():
    """`TFIDFConverter` keeps its scope text column untouched and appends
    one `tfidf_<token>` column per vocabulary term — its group's real
    columns must be only the `tfidf_*` columns, never the untouched
    original text column."""
    df_x = pd.DataFrame({"text": ["cat dog", "dog dog", "cat"], "other": [1, 2, 3]})
    x = {
        "train": _dataset(df_x),
        "test": _dataset(pd.DataFrame({"text": ["cat"], "other": [4]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(TFIDFConverter)
    config = [
        {
            "id": "conv_0",
            "converter": "TFIDFConverter",
            "params": {},
            "input_scope": [{"kind": "column", "name": "text"}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    group_columns = group_registry[("conv_0", 0)][0]
    assert "text" not in group_columns
    assert all(name.startswith("tfidf_") for name in group_columns)
    assert len(group_columns) > 0
    assert "text" in new_x["train"].column_names


def test_group_registry_excludes_untouched_originals_for_column_arithmetic():
    """`ColumnArithmetic` keeps its two operand columns untouched and
    appends a single new result column — its group's real columns must be
    only that new column, never the untouched operands."""
    import pyarrow as pa

    numeric_types = {
        "a": Float(arrow_type=pa.float64()),
        "b": Float(arrow_type=pa.float64()),
    }
    df_x = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    x = {
        "train": _typed_dataset(df_x, numeric_types),
        "test": _typed_dataset(pd.DataFrame({"a": [4.0], "b": [40.0]}), numeric_types),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(ColumnArithmetic)
    config = [
        {
            "id": "conv_0",
            "converter": "ColumnArithmetic",
            "params": {"operation": "add"},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
            ],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    assert group_registry[("conv_0", 0)][0] == ["a_add_b"]
    assert "a" in new_x["train"].column_names
    assert "b" in new_x["train"].column_names


def test_group_registry_excludes_untouched_originals_for_column_concat():
    """`ColumnConcat` keeps its two operand columns untouched and appends a
    single new result column — its group's real columns must be only that
    new column, never the untouched operands."""
    import pyarrow as pa

    text_types = {"a": Text(arrow_type=pa.string()), "b": Text(arrow_type=pa.string())}
    df_x = pd.DataFrame({"a": ["x", "y", "z"], "b": ["1", "2", "3"]})
    x = {
        "train": _typed_dataset(df_x, text_types),
        "test": _typed_dataset(pd.DataFrame({"a": ["w"], "b": ["4"]}), text_types),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(ColumnConcat)
    config = [
        {
            "id": "conv_0",
            "converter": "ColumnConcat",
            "params": {"separator": "_"},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
            ],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    assert group_registry[("conv_0", 0)][0] == ["a_concat_b"]
    assert "a" in new_x["train"].column_names
    assert "b" in new_x["train"].column_names


def test_group_registry_excludes_untouched_originals_for_numeric_expansion():
    """`NumericExpansion` keeps its scope column(s) untouched and appends
    one `{operation}_<col>` column per fitted numeric column — its group's
    real columns must be only the expanded columns, never the untouched
    originals."""
    import pyarrow as pa

    numeric_types = {
        "a": Float(arrow_type=pa.float64()),
        "b": Float(arrow_type=pa.float64()),
    }
    df_x = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
    x = {
        "train": _typed_dataset(df_x, numeric_types),
        "test": _typed_dataset(pd.DataFrame({"a": [7.0], "b": [8.0]}), numeric_types),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1, 0]})),
        "test": _dataset(pd.DataFrame({"target": [1]})),
    }

    registry = _registry(NumericExpansion)
    config = [
        {
            "id": "conv_0",
            "converter": "NumericExpansion",
            "params": {"operation": "square"},
            "input_scope": [{"kind": "column", "name": "a"}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    assert group_registry[("conv_0", 0)][0] == ["square_a"]
    assert "a" in new_x["train"].column_names
    assert "b" in new_x["train"].column_names


class _FoldDependentColumnPicker:
    """Test double: a SUPERVISED converter that keeps only ONE of its two
    input columns, chosen by each fold's own target mean. Lets a test prove
    that a later converter's group reference to this one resolves
    independently per fold, without depending on a real sklearn converter's
    behavior on tiny hand-built data."""

    SUPERVISED = True
    CHANGES_ROW_COUNT = False

    def __init__(self, **kwargs):
        self._picked = None

    def fit(self, x, y=None):
        mean = y.to_pandas().iloc[:, 0].mean()
        self._picked = "a" if mean < 0.5 else "b"
        return self

    def transform(self, x, y=None):
        return x.select_columns([self._picked])

    def get_output_type(self, column_name=None):
        import pyarrow as pa

        return Float(arrow_type=pa.float64())

    def get_output_slots(self):
        return [{"slot": 0, "label": "output", "type": self.get_output_type()}]

    def classify_output_columns(self, real_column_names):
        return {0: list(real_column_names)}


def test_input_scope_group_resolves_independently_per_fold_for_supervised_converter():
    """A SUPERVISED converter's real output can differ per fold (here, which
    of two original columns survives); a later converter's group reference
    to it must resolve using THAT fold's own real columns, not another
    fold's."""
    fold_0_df = pd.DataFrame({"a": [1.0, 2.0], "b": [10.0, 20.0]})
    fold_1_df = pd.DataFrame({"a": [3.0, 4.0], "b": [30.0, 40.0]})
    fold_0 = {
        "train": _dataset(fold_0_df),
        "test": _dataset(pd.DataFrame({"a": [5.0], "b": [50.0]})),
    }
    fold_1 = {
        "train": _dataset(fold_1_df),
        "test": _dataset(pd.DataFrame({"a": [6.0], "b": [60.0]})),
    }
    full_dataset = {
        "train": _dataset(pd.concat([fold_0_df, fold_1_df], ignore_index=True)),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }

    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0]})),
        "test": _dataset(pd.DataFrame({"target": [0.0]})),
    }
    y_fold_1 = {
        "train": _dataset(pd.DataFrame({"target": [1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": [1.0]})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0, 1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, fold_1, full_dataset]
    y = [y_fold_0, y_fold_1, y_full_dataset]

    registry = _registry(_FoldDependentColumnPicker, StandardScaler)
    config = [
        {
            "id": "conv_0",
            "converter": "_FoldDependentColumnPicker",
            "params": {},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
            ],
        },
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    # A mean of 0.0 picks "a", a mean of 1.0 picks "b": different real
    # columns per fold, proving the group resolved independently.
    assert group_registry[("conv_0", 0)][0] == ["a"]
    assert group_registry[("conv_0", 0)][1] == ["b"]

    # conv_1 (StandardScaler) transformed exactly the column conv_0 kept
    # for each fold, so that's the only column left in each fold's train.
    assert new_x[0]["train"].column_names == ["a"]
    assert new_x[1]["train"].column_names == ["b"]


def test_record_group_columns_orders_by_after_columns_position_not_set_hash():
    """Regression test for a real bug: `record_group_columns` used to build
    its recorded column list via `list(added_set | retained_set)`, whose
    order is a Python set-hash implementation detail, not the columns'
    actual physical order. Any caller that later pairs two different
    partitions' recorded lists positionally (exactly what the fit-once
    "Branch B" reuse path does when a referenced group's real columns
    differ per partition — see the two tests below) needs that order to
    reflect real emission order, or the pairing is a coin flip between
    correct and silently swapped. This directly exercises the fixed line:
    the recorded list must follow `after_columns`' own order, deliberately
    NOT alphabetical/insertion order, to prove it isn't accidentally
    "working" via some other coincidental ordering."""

    class _AllInSlotZero:
        def classify_output_columns(self, real_column_names):
            return {0: list(real_column_names)}

    registry: dict = {}
    record_group_columns(
        entry={"id": "conv_x"},
        converter_instance=_AllInSlotZero(),
        before_columns=["z", "y"],
        # "z" is retained (in resolved_scope and still present); "q" and
        # "p" are brand new. Deliberately NOT in alphabetical order, so a
        # set-based reordering would be easy to miss by coincidence.
        after_columns=["q", "z", "p"],
        resolved_scope=["z", "y"],
        group_registry=registry,
        partition_indexes=[0],
    )

    assert registry[("conv_x", 0)][0] == ["q", "z", "p"]


def test_input_scope_group_reference_with_two_divergent_columns_applies_correct_stats():
    """Value-level regression test for the positional-pairing bug: when a
    Branch-B (fit-once) converter's group reference resolves to TWO real
    columns that differ per fold, the fitted instance's per-column
    statistics must be paired with the right physical column in each fold
    — not swapped. Column-name-only assertions (as in the test above this
    one) can't catch a swap: if "a"/"b" got the wrong stats, the output
    would still be named "a"/"b", just numerically wrong. Here every
    column has a distinguishable value scale, so a swap would be
    off by orders of magnitude, not just "close"."""

    class _TwoColumnFoldPicker:
        """Test double: a SUPERVISED converter that keeps a specific PAIR
        of its four input columns, chosen by the fold's own target mean —
        genuinely different real columns per fold (no name overlap at
        all), forcing the rename-and-reuse path."""

        SUPERVISED = True
        CHANGES_ROW_COUNT = False

        def __init__(self, **kwargs):
            self._picked = None

        def fit(self, x, y=None):
            mean = y.to_pandas().iloc[:, 0].mean()
            self._picked = ["a", "b"] if mean < 0.5 else ["c", "d"]
            return self

        def transform(self, x, y=None):
            return x.select_columns(self._picked)

        def get_output_type(self, column_name=None):
            import pyarrow as pa

            return Float(arrow_type=pa.float64())

        def get_output_slots(self):
            return [{"slot": 0, "label": "output", "type": self.get_output_type()}]

        def classify_output_columns(self, real_column_names):
            return {0: list(real_column_names)}

    # fold_0 diverges from full_dataset (picks a/b vs c/d); fold_1 matches
    # full_dataset (both pick c/d), covering both the rename-dance path
    # and the "same real columns" fast path in the same test.
    fold_0_df = pd.DataFrame(
        {
            "a": [1.0, 2.0],
            "b": [10.0, 20.0],
            "c": [1000.0, 2000.0],
            "d": [-1.0, -2.0],
        }
    )
    fold_1_df = pd.DataFrame(
        {
            "a": [3.0, 4.0],
            "b": [30.0, 40.0],
            "c": [3000.0, 4000.0],
            "d": [-3.0, -4.0],
        }
    )
    full_df = pd.concat([fold_0_df, fold_1_df], ignore_index=True)

    fold_0 = {
        "train": _dataset(fold_0_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": [], "c": [], "d": []})),
    }
    fold_1 = {
        "train": _dataset(fold_1_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": [], "c": [], "d": []})),
    }
    full_dataset = {
        "train": _dataset(full_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": [], "c": [], "d": []})),
    }

    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }
    y_fold_1 = {
        "train": _dataset(pd.DataFrame({"target": [1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0, 1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, fold_1, full_dataset]
    y = [y_fold_0, y_fold_1, y_full_dataset]

    registry = _registry(_TwoColumnFoldPicker, StandardScaler)
    config = [
        {
            "id": "conv_0",
            "converter": "_TwoColumnFoldPicker",
            "params": {},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
                {"kind": "column", "name": "c"},
                {"kind": "column", "name": "d"},
            ],
        },
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    # conv_0's real per-fold output, in its own emission order.
    assert group_registry[("conv_0", 0)][0] == ["a", "b"]
    assert group_registry[("conv_0", 0)][1] == ["c", "d"]
    assert group_registry[("conv_0", 0)][2] == ["c", "d"]

    # conv_1 is fit once on full_dataset's ["c", "d"].
    full_expected = SkStandardScaler().fit(
        pd.DataFrame({"c": full_df["c"].tolist(), "d": full_df["d"].tolist()})
    )

    # fold_1 shares the exact same real columns as full_dataset — the fast,
    # no-rename path — so this is the simple sanity check.
    fold_1_transformed = new_x[1]["train"].to_pandas()
    expected_fold_1 = full_expected.transform(
        pd.DataFrame({"c": [3000.0, 4000.0], "d": [-3.0, -4.0]})
    )
    assert fold_1_transformed["c"].tolist() == pytest.approx(
        expected_fold_1[:, 0].tolist()
    )
    assert fold_1_transformed["d"].tolist() == pytest.approx(
        expected_fold_1[:, 1].tolist()
    )

    # fold_0 has NO overlap with full_dataset's real columns ("a"/"b" vs
    # "c"/"d") — the rename-and-reuse path. The correct pairing is by
    # emission POSITION: "a" (conv_0's 1st output for fold_0) gets the
    # statistics fit for "c" (conv_0's 1st output for full_dataset), and
    # "b" (2nd) gets "d"'s (2nd) statistics. A positional swap (the bug)
    # would instead apply "d"'s statistics to "a" and "c"'s to "b" —
    # wildly different numbers, given "c" is ~1000x the scale of "d".
    fold_0_transformed = new_x[0]["train"].to_pandas()
    expected_fold_0_first = full_expected.transform(
        pd.DataFrame({"c": [1.0, 2.0], "d": [10.0, 20.0]})
    )[:, 0]
    expected_fold_0_second = full_expected.transform(
        pd.DataFrame({"c": [1.0, 2.0], "d": [10.0, 20.0]})
    )[:, 1]
    assert fold_0_transformed["a"].tolist() == pytest.approx(
        expected_fold_0_first.tolist()
    )
    assert fold_0_transformed["b"].tolist() == pytest.approx(
        expected_fold_0_second.tolist()
    )


def test_branch_b_group_registry_recorded_per_partition_not_full_dataset_blanket():
    """Regression test for a real bug: a Branch-B (fit-once) converter's
    OWN group registration used to be written identically for every
    partition index using only full_dataset's real columns — even for
    folds where this converter's actual output was a completely different
    real column. A downstream converter referencing THIS converter's group
    would then resolve the wrong (or a nonexistent) column for those
    folds. This chains three converters — a per-fold-divergent Branch A,
    then two Branch-B converters — and checks both the registry contents
    and that the final numeric values are correct (not just that nothing
    crashed)."""
    fold_0_df = pd.DataFrame({"a": [1.0, 2.0], "b": [10.0, 20.0]})
    fold_1_df = pd.DataFrame({"a": [3.0, 4.0], "b": [30.0, 40.0]})
    full_df = pd.concat([fold_0_df, fold_1_df], ignore_index=True)

    fold_0 = {
        "train": _dataset(fold_0_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }
    fold_1 = {
        "train": _dataset(fold_1_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }
    full_dataset = {
        "train": _dataset(full_df),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }

    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }
    y_fold_1 = {
        "train": _dataset(pd.DataFrame({"target": [1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0, 1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, fold_1, full_dataset]
    y = [y_fold_0, y_fold_1, y_full_dataset]

    registry = _registry(_FoldDependentColumnPicker, StandardScaler)
    config = [
        {
            "id": "conv_0",
            "converter": "_FoldDependentColumnPicker",
            "params": {},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
            ],
        },
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        },
        {
            "id": "conv_2",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_1", "slot": 0}],
        },
    ]

    new_x, new_y, fitted, group_registry = apply_session_converters(
        x, y, config, registry
    )

    # conv_0 (unchanged Branch A per-fold logic): fold_0 -> "a", fold_1/
    # full_dataset -> "b".
    assert group_registry[("conv_0", 0)][0] == ["a"]
    assert group_registry[("conv_0", 0)][1] == ["b"]
    assert group_registry[("conv_0", 0)][2] == ["b"]

    # conv_1 is itself a Branch-B (fit-once) converter. THE FIX: its own
    # recorded real column must be fold_0's actual "a" — not full_dataset's
    # "b" blanket-copied onto every index (the bug).
    assert group_registry[("conv_1", 0)][0] == ["a"]
    assert group_registry[("conv_1", 0)][1] == ["b"]
    assert group_registry[("conv_1", 0)][2] == ["b"]

    # conv_2 (also Branch-B, referencing conv_1's group) must have
    # completed without error and resolved fold_0's real column correctly
    # too — proving the fix actually unblocks a second-level reference,
    # not just the registry dict in isolation.
    assert new_x[0]["train"].column_names == ["a"]
    assert new_x[1]["train"].column_names == ["b"]

    # Value-level check: conv_1 fits once on full_dataset's "b"
    # ([10,20,30,40]); conv_2 fits once on conv_1's OWN full_dataset output
    # (that same "b", already scaled once). fold_0's final "a" value must
    # match applying BOTH fitted scalers in sequence — not some other stat.
    conv_1_expected = SkStandardScaler().fit(
        pd.DataFrame({"b": [10.0, 20.0, 30.0, 40.0]})
    )
    full_b_after_conv_1 = conv_1_expected.transform(
        pd.DataFrame({"b": [10.0, 20.0, 30.0, 40.0]})
    ).ravel()
    conv_2_expected = SkStandardScaler().fit(pd.DataFrame({"b": full_b_after_conv_1}))

    fold_0_a_after_conv_1 = conv_1_expected.transform(
        pd.DataFrame({"b": [1.0, 2.0]})
    ).ravel()
    fold_0_a_expected_final = conv_2_expected.transform(
        pd.DataFrame({"b": fold_0_a_after_conv_1})
    ).ravel()

    assert new_x[0]["train"].to_pandas()["a"].tolist() == pytest.approx(
        fold_0_a_expected_final.tolist()
    )


def test_dangling_group_reference_raises_instead_of_silently_using_all_columns():
    """A group atom pointing at a converter_id/slot that never produced
    columns for this partition (e.g. it never ran, or — like
    `SimpleImputer` without `add_indicator` — never emits that slot at
    all) must raise, not silently fall back to "all columns"."""
    x = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0]})),
        "test": _dataset(pd.DataFrame({"a": [3.0]})),
    }
    y = {
        "train": _dataset(pd.DataFrame({"target": [0, 1]})),
        "test": _dataset(pd.DataFrame({"target": [0]})),
    }
    registry = _registry(StandardScaler)
    config = [
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [
                {"kind": "group", "converter_id": "nonexistent_conv", "slot": 0}
            ],
        }
    ]

    with pytest.raises(JobError, match="nonexistent_conv"):
        apply_session_converters(x, y, config, registry)


def test_branch_b_reuse_with_mismatched_column_count_raises():
    """A Branch-B (fit-once) converter whose group reference resolves to a
    DIFFERENT number of columns in some fold than it was fit on cannot be
    reused there at all — no 1:1 pairing exists. This must raise a clear
    JobError, not fall through to an unguarded (and either confusingly
    failing or silently wrong) `.transform()` call."""

    class _VariableColumnCountPicker:
        """SUPERVISED, per-fold: keeps 1 column for one fold, 2 for
        another, so a downstream fit-once converter's group reference
        resolves to differing counts per partition."""

        SUPERVISED = True
        CHANGES_ROW_COUNT = False

        def __init__(self, **kwargs):
            self._picked = None

        def fit(self, x, y=None):
            mean = y.to_pandas().iloc[:, 0].mean()
            self._picked = ["a"] if mean < 0.5 else ["a", "b"]
            return self

        def transform(self, x, y=None):
            return x.select_columns(self._picked)

        def get_output_type(self, column_name=None):
            import pyarrow as pa

            return Float(arrow_type=pa.float64())

        def get_output_slots(self):
            return [{"slot": 0, "label": "output", "type": self.get_output_type()}]

        def classify_output_columns(self, real_column_names):
            return {0: list(real_column_names)}

    fold_0 = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0], "b": [10.0, 20.0]})),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }
    full_dataset = {
        "train": _dataset(pd.DataFrame({"a": [1.0, 2.0], "b": [10.0, 20.0]})),
        "test": _dataset(pd.DataFrame({"a": [], "b": []})),
    }
    y_fold_0 = {
        "train": _dataset(pd.DataFrame({"target": [0.0, 0.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }
    y_full_dataset = {
        "train": _dataset(pd.DataFrame({"target": [1.0, 1.0]})),
        "test": _dataset(pd.DataFrame({"target": []})),
    }

    x = [fold_0, full_dataset]
    y = [y_fold_0, y_full_dataset]

    registry = _registry(_VariableColumnCountPicker, StandardScaler)
    config = [
        {
            "id": "conv_0",
            "converter": "_VariableColumnCountPicker",
            "params": {},
            "input_scope": [
                {"kind": "column", "name": "a"},
                {"kind": "column", "name": "b"},
            ],
        },
        {
            "id": "conv_1",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        },
    ]

    with pytest.raises(JobError, match="differing number of columns"):
        apply_session_converters(x, y, config, registry)


def test_apply_session_converters_noop_without_config():
    x = {"train": _dataset(pd.DataFrame({"a": [1.0]}))}
    y = {"train": _dataset(pd.DataFrame({"target": [0]}))}
    new_x, new_y, fitted, _group_registry = apply_session_converters(x, y, [], {})
    assert new_x is x
    assert new_y is y
    assert fitted == []


def test_save_load_and_transform_for_prediction_round_trip(tmp_path):
    """The full prediction-time story: fit on train, save to disk next to a
    (fake) model path, load it back, and replay it on brand-new data."""
    x_train = _dataset(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]}))
    y_train = _dataset(pd.DataFrame({"target": [0, 1, 0, 1]}))

    registry = _registry(StandardScaler)
    config = [_converter_config("StandardScaler")]

    _, _, _, fitted = fit_transform_on_partition(config, registry, x_train, y_train)

    run_path = str(tmp_path / "42")  # sklearn-style: a plain file path, no dir.
    saved_path = save_fitted_converters(run_path, fitted)
    assert saved_path == f"{run_path}_converters.pkl"
    assert os.path.exists(saved_path)

    loaded = load_fitted_converters(run_path)
    assert len(loaded) == 1

    new_input = _dataset(pd.DataFrame({"a": [100.0, 200.0]}))
    transformed = transform_for_prediction(new_input, loaded)

    expected = SkStandardScaler().fit(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]}))
    assert transformed.to_pandas()["a"].tolist() == pytest.approx(
        expected.transform(pd.DataFrame({"a": [100.0, 200.0]})).ravel().tolist()
    )


def test_save_fitted_converters_noop_when_empty(tmp_path):
    run_path = str(tmp_path / "42")
    assert save_fitted_converters(run_path, []) is None
    assert not os.path.exists(fitted_converters_path(run_path))


def test_load_fitted_converters_missing_file_returns_empty(tmp_path):
    run_path = str(tmp_path / "does-not-exist")
    assert load_fitted_converters(run_path) == []


def test_transform_for_prediction_skips_samplers_by_construction():
    """Samplers never end up in `fitted_converters` (see
    test_sampler_only_changes_train_not_test_or_validation), so replaying an
    empty list on new prediction input is simply a no-op."""
    new_input = _dataset(pd.DataFrame({"a": [1.0, 2.0]}))
    result = transform_for_prediction(new_input, [])
    assert result.to_pandas()["a"].tolist() == [1.0, 2.0]
