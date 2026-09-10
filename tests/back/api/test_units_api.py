"""The atomic units are exposed as regular registry components."""

import pytest
from fastapi.testclient import TestClient

EXPECTED_UNITS = {
    "LoadDatasetUnit",
    "PrepareAndSplitUnit",
    "PrepareAndFoldUnit",
    "BuildModelUnit",
    "FitModelUnit",
    "FitModelOverFoldsUnit",
    "EvaluateModelUnit",
    "EvaluateModelToArtifactUnit",
    "SaveModelUnit",
    "ApplyConverterUnit",
    "FitConverterUnit",
    "TransformDatasetUnit",
    "SaveDatasetUnit",
    "RunExplorationUnit",
    "SaveExplorationUnit",
    "LoadTrainedModelUnit",
    "LoadTrainingDatasetUnit",
    "BuildManualInputUnit",
    "PredictUnit",
    "SavePredictionUnit",
    "LoadRunModelUnit",
    "BuildGlobalExplainerUnit",
    "BuildLocalExplainerUnit",
    "PrepareExplanationDataUnit",
    "GenerateGlobalExplanationUnit",
    "GenerateLocalExplanationUnit",
    "LoadUploadedDatasetUnit",
    "LoadDatafileDatasetUnit",
    "InferDatasetTypesUnit",
    "ApplyDatasetSchemaUnit",
    "ComputeDatasetMetadataUnit",
    "SaveDatasetToPathUnit",
}


@pytest.fixture(name="units", scope="module")
def get_units(client: TestClient):
    response = client.get("/api/v1/component/?select_types=Unit")
    assert response.status_code == 200, response.text
    return {component["name"]: component for component in response.json()}


def test_every_unit_is_registered(units):
    assert set(units) == EXPECTED_UNITS


def test_units_are_registered_under_the_unit_type(units):
    for unit in units.values():
        assert unit["type"] == "Unit"


def test_units_expose_a_schema_the_front_can_render(units):
    for name, unit in units.items():
        assert unit["configurable_object"] is True, name
        assert "properties" in unit["schema"], name


def test_unit_schemas_describe_their_configuration(units):
    assert set(units["LoadDatasetUnit"]["schema"]["properties"]) == {
        "dataset_id",
        "notebook_id",
    }
    # The two splitting units are the same form with a different family of
    # splitters offered, which is the whole of what separates them.
    for name in ("PrepareAndSplitUnit", "PrepareAndFoldUnit"):
        assert set(units[name]["schema"]["properties"]) == {
            "task_name",
            "input_columns",
            "output_columns",
            "splitter",
        }, name
    assert (
        units["PrepareAndSplitUnit"]["schema"]["properties"]["splitter"]["parent"]
        == "PartitionSplitter"
    )
    assert (
        units["PrepareAndFoldUnit"]["schema"]["properties"]["splitter"]["parent"]
        == "FoldSplitter"
    )
    assert "model" in units["BuildModelUnit"]["schema"]["properties"]
    assert "optimizer" in units["FitModelUnit"]["schema"]["properties"]
    assert set(units["ApplyConverterUnit"]["schema"]["properties"]) == {
        "converter",
        "scope",
        "target",
    }
    assert set(units["FitConverterUnit"]["schema"]["properties"]) == {
        "converter",
        "scope",
        "target",
    }
    # No converter to pick: it arrives already fitted through the context.
    assert set(units["TransformDatasetUnit"]["schema"]["properties"]) == {
        "scope",
        "target",
    }
    # SaveDatasetUnit is configuration-free: it saves where the load said.
    assert units["SaveDatasetUnit"]["schema"]["properties"] == {}
    assert set(units["RunExplorationUnit"]["schema"]["properties"]) == {
        "explorer_id",
        "explorer",
    }
    # SaveExplorationUnit only picks the destination; how the result is
    # serialised belongs to the explorer that produced it.
    assert set(units["SaveExplorationUnit"]["schema"]["properties"]) == {"explorer_id"}
    assert set(units["LoadTrainedModelUnit"]["schema"]["properties"]) == {"run_id"}
    assert set(units["PredictUnit"]["schema"]["properties"]) == {
        "task_name",
        "input_columns",
        "output_columns",
    }
    assert set(units["SavePredictionUnit"]["schema"]["properties"]) == {
        "input_columns",
        "output_columns",
    }
    assert set(units["BuildGlobalExplainerUnit"]["schema"]["properties"]) == {
        "explainer"
    }
    assert set(units["BuildLocalExplainerUnit"]["schema"]["properties"]) == {
        "explainer"
    }
    assert set(units["GenerateGlobalExplanationUnit"]["schema"]["properties"]) == {
        "explainer_id"
    }
    # temp_path is a runtime param: the endpoint makes the directory, so it
    # never reaches the schema the front receives.
    assert set(units["LoadUploadedDatasetUnit"]["schema"]["properties"]) == {
        "dataloader",
        "source",
        "n_sample",
    }
    assert set(units["LoadDatafileDatasetUnit"]["schema"]["properties"]) == {
        "dataloader",
        "datafile_id",
        "selected_file",
    }
    assert set(units["InferDatasetTypesUnit"]["schema"]["properties"]) == {"method"}
    # The type declaration arrives through the context, not the configuration,
    # so the only thing to configure here is the renaming.
    assert set(units["ApplyDatasetSchemaUnit"]["schema"]["properties"]) == {
        "column_renames"
    }
    assert set(units["ComputeDatasetMetadataUnit"]["schema"]["properties"]) == {
        "compute_metadata",
    }
    # The sibling of SaveDatasetUnit: that one saves where the load said, this
    # one is told where to save. The destination stays user-facing: a job
    # happens to compute it, but on a canvas picking where to store a dataset
    # is a decision, and a value a user can know while filling the form in.
    assert set(units["SaveDatasetToPathUnit"]["schema"]["properties"]) == {"path"}


def test_component_fields_tell_the_front_which_components_to_offer(units):
    """The recursive part of the schema system.

    A component field does not inline the chosen component's schema; it
    carries a ``parent`` hint so the front can list the candidates and then
    fetch that component's own schema to render the nested form.
    """
    model = units["BuildModelUnit"]["schema"]["properties"]["model"]
    optimizer = units["FitModelUnit"]["schema"]["properties"]["optimizer"]
    converter = units["ApplyConverterUnit"]["schema"]["properties"]["converter"]
    explorer = units["RunExplorationUnit"]["schema"]["properties"]["explorer"]

    uploaded = units["LoadUploadedDatasetUnit"]["schema"]["properties"]["dataloader"]
    datafile = units["LoadDatafileDatasetUnit"]["schema"]["properties"]["dataloader"]

    assert model["parent"] == "BaseModel"
    assert optimizer["parent"] == "BaseOptimizer"
    assert converter["parent"] == "BaseConverter"
    assert explorer["parent"] == "BaseExplorer"
    # Both loading units offer the same readers; what differs is how each one
    # finds the bytes to hand them.
    assert uploaded["parent"] == "BaseDataLoader"
    assert datafile["parent"] == "BaseDataLoader"

    # Global and local explainers are separate registries with separate base
    # classes, and a component field carries a single parent hint. Hence two
    # sibling units with one required field each: making a single field cover
    # both scopes would need it to be optional, and an optional component field
    # is emitted as an anyOf, which hides the hint from the front — that is what
    # the assertions below would catch.
    global_explainer = units["BuildGlobalExplainerUnit"]["schema"]["properties"]
    local_explainer = units["BuildLocalExplainerUnit"]["schema"]["properties"]
    assert global_explainer["explainer"]["parent"] == "BaseGlobalExplainer"
    assert local_explainer["explainer"]["parent"] == "BaseLocalExplainer"
    assert set(model["properties"]) == {"component", "params"}
    assert set(converter["properties"]) == {"component", "params"}


def test_a_component_field_parent_resolves_to_real_components(client: TestClient):
    response = client.get("/api/v1/component/?component_parent=BaseOptimizer")
    assert response.status_code == 200, response.text

    names = {component["name"] for component in response.json()}
    assert "OptunaOptimizer" in names


def test_units_do_not_leak_into_the_job_listing(client: TestClient):
    response = client.get("/api/v1/component/?select_types=Job")
    assert response.status_code == 200, response.text

    job_names = {component["name"] for component in response.json()}
    assert not (job_names & EXPECTED_UNITS)
    assert "ModelJob" in job_names


@pytest.fixture(name="unit_classes", scope="module")
def get_unit_classes(client: TestClient):
    """The registered classes behind the response, from the same registry."""
    registry = client.app.container["component_registry"]
    return {name: registry[name]["class"] for name in EXPECTED_UNITS}


#: Every runtime param in the palette. Configuration supplied by whatever runs
#: the unit -- a job, the DAG engine, an endpoint -- and never by a user,
#: because at the moment a form would be filled in the value is not knowable:
#: a path a job has yet to choose, a foreign key to a row nobody has seen, or
#: a name built from the id of a run that has not started.
EXPECTED_RUNTIME_PARAMS = {
    ("LoadUploadedDatasetUnit", "temp_path"),
    ("LoadTrainingDatasetUnit", "train_dataset_file_path"),
    ("BuildManualInputUnit", "train_dataset_file_path"),
    ("GenerateLocalExplanationUnit", "session_splits"),
    ("ComputeDatasetMetadataUnit", "trust_inherited_metadata"),
    ("BuildModelUnit", "run_id"),
    ("EvaluateModelUnit", "run_id"),
    ("FitModelUnit", "run_id"),
    ("FitModelOverFoldsUnit", "run_id"),
    ("FitModelOverFoldsUnit", "artifact_prefix"),
    ("FitModelUnit", "artifact_prefix"),
    ("SaveModelUnit", "artifact_prefix"),
}


def test_the_runtime_params_are_exactly_the_declared_ones(unit_classes):
    """Adding or removing one has to be a deliberate edit, not a side effect."""
    declared = {
        (name, param)
        for name, cls in unit_classes.items()
        for param in cls.RUNTIME_PARAMS
    }

    assert declared == EXPECTED_RUNTIME_PARAMS


def test_no_runtime_param_reaches_the_schema_the_front_receives(units, unit_classes):
    """The guarantee the whole arrangement exists for.

    A flag inside the schema would have left these on the wire, where every
    renderer has to remember to skip them and a new one leaks by default. Being
    a separate declaration means there is nothing to filter: the name is simply
    not in what the front is given.
    """
    for name, cls in unit_classes.items():
        exposed = set(units[name]["schema"]["properties"])
        leaked = exposed & set(cls.RUNTIME_PARAMS)

        assert not leaked, (
            f"{name} exposes {sorted(leaked)} in the schema the front renders, "
            "even though it is declared as supplied by whatever runs the unit."
        )


def test_a_unit_can_have_no_user_configuration_at_all(units):
    """Which is a real shape, not a degenerate one.

    Three units are told everything by their caller, and SaveDatasetUnit was
    already configuration-free before any of this. An empty schema is valid and
    renders as nothing.
    """
    for name in ("SaveModelUnit", "LoadTrainingDatasetUnit", "SaveDatasetUnit"):
        assert units[name]["schema"]["properties"] == {}, name
        assert units[name]["configurable_object"] is True, name
