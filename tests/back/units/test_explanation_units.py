"""Contract tests for the explanation units, isolated from any orchestrating job.

The context is built by hand rather than through a job, which is what exposes
composability mistakes: a job always wires the context "correctly", so an
end-to-end run cannot tell a real contract from a lucky one.
"""

import json
import pickle
from pathlib import Path

import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.units.build_global_explainer_unit import BuildGlobalExplainerUnit
from DashAI.back.units.build_local_explainer_unit import BuildLocalExplainerUnit
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.generate_global_explanation_unit import (
    GenerateGlobalExplanationUnit,
)
from DashAI.back.units.generate_local_explanation_unit import (
    GenerateLocalExplanationUnit,
)
from DashAI.back.units.load_run_model_unit import LoadRunModelUnit
from DashAI.back.units.prepare_explanation_data_unit import PrepareExplanationDataUnit

SPLITS = {
    "train_indexes": [0, 1, 2],
    "test_indexes": [3, 4],
    "val_indexes": [5],
}


class _RunRow:
    def __init__(
        self, model_name="RecordingModel", run_path="somewhere", parameters=None
    ):
        self.id = 5
        self.model_name = model_name
        self.run_path = run_path
        self.parameters = parameters if parameters is not None else {"depth": 3}


class _DatasetRow:
    def __init__(self, file_path):
        self.file_path = file_path


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(model.__name__, {}).get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """Stand-in for a ``sessionmaker``.

    A class rather than a lambda on purpose: kink invokes any registered lambda
    with the container to resolve it.
    """

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


class RecordingModel:
    """Model that records how it was built and what it was asked to encode."""

    built_with = None

    def __init__(self, **kwargs):
        RecordingModel.built_with = kwargs

    @staticmethod
    def load(filename):
        # Bypasses __init__ on purpose: this is what every real model does —
        # joblib or a checkpoint rebuilds the object, and the instance the unit
        # constructed beforehand is thrown away. Going through __init__ here
        # would overwrite the record of how that instance was built.
        model = object.__new__(RecordingModel)
        model.loaded_from = filename
        return model

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class UninstantiableModel(RecordingModel):
    def __init__(self, **kwargs):
        raise RuntimeError("this model refuses to be built")


class UnloadableModel(RecordingModel):
    @staticmethod
    def load(filename):
        raise OSError("the artifact is not there")


class RecordingTask:
    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        return dataset

    def process_manual_input(self, rows, dataset_path):
        import pandas as pd
        import pyarrow as pa

        from DashAI.back.types.value_types import Integer

        frame = pd.DataFrame(rows)
        types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
        return to_dashai_dataset(frame, types=types)


class RecordingGlobalExplainer:
    def __init__(self, model, **kwargs):
        self.model = model
        self.kwargs = kwargs
        self.seen = None

    def explain(self, dataset):
        self.seen = dataset
        return {"importance": [1, 2]}

    def plot(self, explanation):
        return "a plot"


class ExplodingGlobalExplainer(RecordingGlobalExplainer):
    def explain(self, dataset):
        raise RuntimeError("the explanation itself blew up")


class RecordingLocalExplainer:
    fitted_with = None

    def __init__(self, model, **kwargs):
        self.model = model
        self.explained_columns = None

    def fit(self, dataset, **kwargs):
        RecordingLocalExplainer.fitted_with = kwargs
        return self

    def explain_instance(self, instances):
        columns = instances.column_names
        if isinstance(columns, dict):
            columns = [c for split in columns.values() for c in split]
        self.explained_columns = columns
        return {"local": True}

    def plot(self, explanation):
        return "a plot"


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "RecordingModel": {"class": RecordingModel},
        "UninstantiableModel": {"class": UninstantiableModel},
        "UnloadableModel": {"class": UnloadableModel},
        "RecordingTask": {"class": RecordingTask},
        "RecordingGlobalExplainer": {"class": RecordingGlobalExplainer},
        "ExplodingGlobalExplainer": {"class": ExplodingGlobalExplainer},
        "RecordingLocalExplainer": {"class": RecordingLocalExplainer},
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def _dataset(rows=6):
    import pandas as pd
    import pyarrow as pa

    from DashAI.back.types.value_types import Integer

    frame = pd.DataFrame(
        {"a": list(range(rows)), "b": list(range(rows)), "target": [0, 1] * (rows // 2)}
    )
    types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


@pytest.fixture(name="stored_instances")
def fixture_stored_instances(tmp_path):
    root = tmp_path / "instances"
    save_dataset(_dataset(), str(root / "dataset"))
    return root


@pytest.fixture(name="fake_db")
def fixture_fake_db(stored_instances):
    rows = {
        "Run": {5: _RunRow()},
        "Dataset": {9: _DatasetRow(str(stored_instances))},
    }
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


@pytest.fixture(name="explanations_path")
def fixture_explanations_path(tmp_path):
    target = tmp_path / "explanations"
    target.mkdir()
    di["config"] = {"EXPLANATIONS_PATH": target}
    yield target
    del di["config"]


# --- LoadRunModelUnit ---------------------------------------------------


def test_the_run_model_is_built_with_its_parameters_before_loading(registry, fake_db):
    """The extra construction step is the difference from ``LoadTrainedModelUnit``.

    It has no effect for models whose ``load`` is a static or class method — all
    of the real ones — but it is the inherited behaviour of this flow, and this
    test is what would notice if the two units were quietly merged.
    """
    ctx = ExecutionContext()
    RecordingModel.built_with = None

    LoadRunModelUnit(run_id=5)(ctx)

    assert RecordingModel.built_with == {"depth": 3}
    assert ctx.require("model").loaded_from == "somewhere"


def test_a_missing_run_is_reported_by_id(registry, fake_db):
    with pytest.raises(JobError, match="Run 99 does not exist in DB."):
        LoadRunModelUnit(run_id=99)(ExecutionContext())


def test_an_unknown_model_name_uses_the_explanation_wording(registry, fake_db):
    """Word for word different from ``LoadTrainedModelUnit``'s message, which is
    why the two units are not merged."""
    fake_db["Run"][5].model_name = "NoSuchModel"

    with pytest.raises(
        JobError, match="Unable to find Model with name NoSuchModel in registry."
    ):
        LoadRunModelUnit(run_id=5)(ExecutionContext())


def test_a_model_that_cannot_be_built_is_reported_separately_from_loading(
    registry, fake_db
):
    fake_db["Run"][5].model_name = "UninstantiableModel"

    with pytest.raises(JobError, match="Unable to instantiate model") as excinfo:
        LoadRunModelUnit(run_id=5)(ExecutionContext())

    assert "refuses to be built" in str(excinfo.value.__cause__)


def test_a_model_that_cannot_be_loaded_names_the_path(registry, fake_db):
    fake_db["Run"][5].model_name = "UnloadableModel"
    fake_db["Run"][5].run_path = "gone"

    with pytest.raises(JobError, match="Can not load model from path gone"):
        LoadRunModelUnit(run_id=5)(ExecutionContext())


# --- the two build units ------------------------------------------------


def test_the_global_build_unit_binds_the_model_from_the_context(registry):
    ctx = ExecutionContext()
    model = RecordingModel()
    ctx.put("model", model)

    BuildGlobalExplainerUnit(
        explainer={"component": "RecordingGlobalExplainer", "params": {"n": 5}}
    )(ctx)

    explainer = ctx.require("explainer")
    assert explainer.model is model
    assert explainer.kwargs == {"n": 5}


def test_the_local_build_unit_produces_the_same_context_key(registry):
    """Both scopes publish ``explainer``, so whatever generates the explanation
    afterwards does not have to know which one ran."""
    ctx = ExecutionContext()
    ctx.put("model", RecordingModel())

    BuildLocalExplainerUnit(
        explainer={"component": "RecordingLocalExplainer", "params": {}}
    )(ctx)

    assert isinstance(ctx.require("explainer"), RecordingLocalExplainer)


def test_building_without_a_model_is_rejected_before_it_starts(registry):
    with pytest.raises(UnitContractError, match="Context key 'model'"):
        BuildGlobalExplainerUnit(
            explainer={"component": "RecordingGlobalExplainer", "params": {}}
        )(ExecutionContext())


def test_each_build_unit_names_its_own_scope_in_its_errors(registry):
    """The messages are worded per scope and are user-visible."""
    ctx = ExecutionContext()
    ctx.put("model", RecordingModel())

    with pytest.raises(JobError, match="Unable to find the global explainer with name"):
        BuildGlobalExplainerUnit(
            explainer={"component": "NoSuchExplainer", "params": {}}
        )(ctx)

    with pytest.raises(JobError, match="Unable to find the local explainer with name"):
        BuildLocalExplainerUnit(
            explainer={"component": "NoSuchExplainer", "params": {}}
        )(ctx)


# --- PrepareExplanationDataUnit -----------------------------------------


def _prepared_context(registry):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset())
    ctx.put("model", RecordingModel())
    ctx.put_ref("dataset_id", 9)
    ctx.put_ref("split_indexes", SPLITS)
    return ctx


def _prepare_unit(**overrides):
    config = {
        "task_name": "RecordingTask",
        "input_columns": ["a", "b"],
        "output_columns": ["target"],
    }
    config.update(overrides)
    return PrepareExplanationDataUnit(**config)


def test_prepare_replays_the_recorded_split(registry):
    """The indexes come from the run, not from a ratio: the explanation has to
    be about the rows the model actually saw."""
    ctx = _prepared_context(registry)

    _prepare_unit()(ctx)

    data_x = ctx.require("data_x")
    assert sorted(data_x.keys()) == ["test", "train", "validation"]
    assert len(data_x["train"]) == 3
    assert len(data_x["test"]) == 2
    assert len(data_x["validation"]) == 1
    assert data_x["train"].column_names == ["a", "b"]
    assert ctx.require("data_y")["train"].column_names == ["target"]


def test_prepare_publishes_the_task_for_the_local_path(registry):
    ctx = _prepared_context(registry)

    _prepare_unit()(ctx)

    assert isinstance(ctx.require("task"), RecordingTask)


def test_prepare_validates_the_task_before_it_runs(registry):
    """``validate`` is called by the orchestrator outside the block that wraps
    preparation failures, so a missing task stays a registry error."""
    with pytest.raises(
        JobError, match="Unable to find Task with name NoSuchTask in registry"
    ):
        _prepare_unit(task_name="NoSuchTask").validate(ExecutionContext())


def test_prepare_without_split_indexes_is_rejected_before_it_starts(registry):
    """A missing key means "nothing published them", not "there is no split"."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset())
    ctx.put("model", RecordingModel())
    ctx.put_ref("dataset_id", 9)

    with pytest.raises(UnitContractError, match="Context key 'split_indexes'"):
        _prepare_unit()(ctx)


def test_prepare_without_a_model_is_rejected_before_it_starts(registry):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset())
    ctx.put_ref("dataset_id", 9)
    ctx.put_ref("split_indexes", SPLITS)

    with pytest.raises(UnitContractError, match="Context key 'model'"):
        _prepare_unit()(ctx)


def test_prepare_composes_after_a_loader_that_publishes_no_dataset_id(registry):
    """A dataset with no id attached is enough to run.

    ``REQUIRES`` is demanded unconditionally, so listing a key the unit never
    reads would silently restrict what it can follow. ``BuildManualInputUnit``
    publishes ``dataset`` alone, and this unit has to work after it.
    """
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset())
    ctx.put("model", RecordingModel())
    ctx.put_ref("split_indexes", SPLITS)

    _prepare_unit()(ctx)

    assert not ctx.has("dataset_id")
    assert len(ctx.require("data_x")["train"]) == 3


# --- GenerateGlobalExplanationUnit --------------------------------------


def test_the_global_explanation_pickles_both_artifacts(registry, explanations_path):
    ctx = ExecutionContext()
    explainer = RecordingGlobalExplainer(RecordingModel())
    ctx.put("explainer", explainer)
    ctx.put("data_x", {"train": 1})
    ctx.put("data_y", {"train": 2})

    GenerateGlobalExplanationUnit(explainer_id=7)(ctx)

    explanation_path = Path(ctx.require("explanation_path"))
    plot_path = Path(ctx.require("plot_path"))
    assert explanation_path.name == "global_explanation_7.pickle"
    assert plot_path.name == "global_explanation_plot_7.pickle"

    with open(explanation_path, "rb") as handle:
        assert pickle.load(handle) == {"importance": [1, 2]}
    # The explainer receives the two halves as a pair, in order.
    assert explainer.seen == ({"train": 1}, {"train": 2})


def test_the_global_unit_never_writes_the_row(registry, explanations_path):
    """It publishes where it wrote; the row belongs to the job.

    The unit takes only an id, so there is nothing for it to write a row with —
    which is the point.
    """
    assert set(GenerateGlobalExplanationUnit.SCHEMA.model_fields) == {"explainer_id"}
    assert GenerateGlobalExplanationUnit.PROVIDES == (
        "explanation_path",
        "plot_path",
    )


def test_a_failing_global_explanation_is_wrapped(registry, explanations_path):
    ctx = ExecutionContext()
    ctx.put("explainer", ExplodingGlobalExplainer(RecordingModel()))
    ctx.put("data_x", {})
    ctx.put("data_y", {})

    with pytest.raises(JobError, match="Failed to generate the explanation") as excinfo:
        GenerateGlobalExplanationUnit(explainer_id=7)(ctx)

    assert "the explanation itself blew up" in str(excinfo.value.__cause__)


def test_generating_without_an_explainer_is_rejected_before_it_starts(
    registry, explanations_path
):
    ctx = ExecutionContext()
    ctx.put("data_x", {})
    ctx.put("data_y", {})

    with pytest.raises(UnitContractError, match="Context key 'explainer'"):
        GenerateGlobalExplanationUnit(explainer_id=7)(ctx)


# --- GenerateLocalExplanationUnit ---------------------------------------


def _local_context(registry):
    ctx = ExecutionContext()
    ctx.put("explainer", RecordingLocalExplainer(RecordingModel()))
    ctx.put("task", RecordingTask())
    ctx.put("data_x", {"train": 1})
    ctx.put("data_y", {"train": 2})
    ctx.put_ref("split_indexes", SPLITS)
    return ctx


def _local_unit(**overrides):
    config = {
        "explainer_id": 7,
        "instance_dataset_id": 9,
        "scope": {"split": "test", "percentage": 100},
        "fit_parameters": {"nsamples": 10},
        "input_columns": ["a", "b"],
        "output_columns": ["target"],
        "manual_input_data": None,
        "same_dataset": True,
        "session_splits": None,
    }
    config.update(overrides)
    return GenerateLocalExplanationUnit(**config)


def test_the_local_explanation_writes_three_artifacts(
    registry, fake_db, explanations_path
):
    ctx = _local_context(registry)

    _local_unit()(ctx)

    assert Path(ctx.require("explanation_path")).name == "local_explanation_7.pickle"
    assert Path(ctx.require("plots_path")).name == "local_explanation_plots_7.pickle"

    saved = load_dataset(str(Path(ctx.require("input_dataset_path")) / "dataset"))
    assert saved.column_names == ["a", "b"]
    assert len(saved) == 2


def test_the_local_explanation_forwards_its_fit_parameters(
    registry, fake_db, explanations_path
):
    ctx = _local_context(registry)
    RecordingLocalExplainer.fitted_with = None

    _local_unit()(ctx)

    assert RecordingLocalExplainer.fitted_with == {"nsamples": 10}


def test_instances_from_another_dataset_recompute_the_split(
    registry, fake_db, explanations_path
):
    """The run's row indexes are meaningless over a different dataset.

    When the instances do not come from the dataset the model was trained on,
    replaying ``split_indexes`` would address rows that do not correspond, so
    the split is recomputed from the session's ratios over the dataset in hand.
    That derived state is resolved inside ``execute`` and never published — this
    is the branch that proves the recompute actually happens.
    """
    ctx = _local_context(registry)

    _local_unit(
        same_dataset=False,
        session_splits=json.dumps(
            {
                "train": 0.5,
                "test": 0.5,
                "validation": 0.0,
                "is_random": True,
                "has_changed": True,
                "seed": 42,
                "shuffle": True,
                "stratify": False,
            }
        ),
        scope={"split": "test", "percentage": 100},
    )(ctx)

    saved = load_dataset(str(Path(ctx.require("input_dataset_path")) / "dataset"))
    # Half of the six stored rows, not the two the run's test_indexes name.
    assert len(saved) == 3
    # The recomputed split never leaks back into the context.
    assert ctx.require("split_indexes") == SPLITS


def test_a_rows_scope_selects_exactly_the_valid_indexes(
    registry, fake_db, explanations_path
):
    ctx = _local_context(registry)

    _local_unit(scope={"mode": "rows", "row_indexes": [0, 3, 5]})(ctx)

    saved = load_dataset(str(Path(ctx.require("input_dataset_path")) / "dataset"))
    assert len(saved) == 3


def test_a_manual_scope_builds_the_instances_from_the_given_rows(
    registry, fake_db, explanations_path
):
    ctx = _local_context(registry)

    _local_unit(
        scope={"mode": "manual"},
        manual_input_data=[{"a": 1, "b": 2}, {"a": 3, "b": 4}],
    )(ctx)

    saved = load_dataset(str(Path(ctx.require("input_dataset_path")) / "dataset"))
    assert saved.column_names == ["a", "b"]
    assert len(saved) == 2


def test_the_three_selection_complaints_are_swallowed_by_one_wrapper(
    registry, fake_db, explanations_path
):
    """All three modes report through the same message, keeping their own
    complaint only as ``__cause__``. Pinned because it is an easy detail to
    "fix" by accident."""
    cases = [
        ({"split": "notasplit", "percentage": 100}, None, "not a valid split"),
        (
            {"mode": "rows", "row_indexes": [10**9]},
            None,
            "No valid row indexes provided",
        ),
        ({"mode": "manual"}, None, "No manual input data provided"),
    ]

    for scope, manual, cause in cases:
        ctx = _local_context(registry)
        with pytest.raises(JobError, match="Can not prepare Dataset with") as excinfo:
            _local_unit(scope=scope, manual_input_data=manual)(ctx)
        assert cause in str(excinfo.value.__cause__), scope


def test_a_missing_instance_dataset_is_reported_by_id(
    registry, fake_db, explanations_path
):
    ctx = _local_context(registry)

    with pytest.raises(
        JobError, match="Dataset 99 to be explained does not exist in DB."
    ):
        _local_unit(instance_dataset_id=99)(ctx)


def test_the_local_unit_needs_the_task_and_says_so(
    registry, fake_db, explanations_path
):
    """The manual mode calls into the task, so it is a declared requirement even
    though the other two modes barely touch it."""
    ctx = ExecutionContext()
    ctx.put("explainer", RecordingLocalExplainer(RecordingModel()))
    ctx.put("data_x", {"train": 1})
    ctx.put("data_y", {"train": 2})
    ctx.put_ref("split_indexes", SPLITS)

    with pytest.raises(UnitContractError, match="Context key 'task'"):
        _local_unit()(ctx)


def test_the_published_paths_are_plain_strings(registry, fake_db, explanations_path):
    """All three travel as refs, so they have to be JSON data."""
    ctx = _local_context(registry)

    _local_unit()(ctx)

    refs = ctx.to_dict()
    for key in ("explanation_path", "plots_path", "input_dataset_path"):
        assert isinstance(refs[key], str), key
