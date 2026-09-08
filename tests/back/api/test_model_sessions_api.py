import json
import os

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession

INPUT_COLUMNS = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
OUTPUT_COLUMNS = ["Species"]

HOLDOUT_SPLITS = {
    "train": 0.6,
    "test": 0.2,
    "validation": 0.2,
    "is_random": True,
    "has_changed": True,
    "seed": 42,
    "shuffle": True,
    "stratify": False,
    "splitType": "random",
    "splitter_name": "HoldoutSplitter",
}


def test_model_session_can_be_created_without_columns(
    client: TestClient, dataset_1: Dataset
) -> None:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="No Columns Yet",
            task_name="TabularClassificationTask",
            input_columns=None,
            output_columns=None,
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits="{}",
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        assert model_session.input_columns is None
        assert model_session.output_columns is None
        db.delete(model_session)
        db.commit()


def test_create_session_without_columns(client: TestClient, dataset_1: Dataset) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Step 1 Only",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": "{}",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["input_columns"] == []
    assert body["output_columns"] == []


def test_put_converters_persists_without_enqueuing_job(
    client: TestClient, dataset_1: Dataset
) -> None:
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Converters PUT Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [
                        {"kind": "column", "name": c} for c in INPUT_COLUMNS
                    ],
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["converters"] == [
        {
            "id": "conv_0",
            "converter": "StandardScaler",
            "params": {},
            "input_scope": [
                {"kind": "column", "name": c, "converter_id": None, "slot": None}
                for c in INPUT_COLUMNS
            ],
            "target_column": None,
        }
    ]
    assert response.json()["preprocessing_huey_id"] is None


def test_put_converters_rejects_unknown_column_atom(
    client: TestClient, dataset_1: Dataset
) -> None:
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Unknown Column Atom Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "does_not_exist"}],
                }
            ]
        },
    )
    assert response.status_code == 422


def test_put_converters_rejects_group_referencing_unknown_converter(
    client: TestClient, dataset_1: Dataset
) -> None:
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Unknown Group Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "does_not_exist", "slot": 0}
                    ],
                }
            ]
        },
    )
    assert response.status_code == 422


def test_put_converters_rejects_type_incompatible_atom(
    client: TestClient, dataset_1: Dataset
) -> None:
    """BagOfWords only accepts Text; pointing it at a numeric column (iris'
    SepalLengthCm) must be rejected at config time, no execution needed."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Type Incompatible Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "BagOfWordsConverter",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )
    assert response.status_code == 422


def test_put_converters_accepts_valid_group_reference_and_does_not_enqueue_job(
    client: TestClient, dataset_1: Dataset
) -> None:
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Valid Group Reference Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                },
                {
                    "id": "conv_1",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "conv_0", "slot": 0}
                    ],
                },
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["converters"]) == 2
    # No job enqueued from this endpoint anymore: preprocessing only runs
    # once the wizard finalizes (Task 5).
    assert body["preprocessing_status"] == 0  # NOT_STARTED
    assert body["preprocessing_huey_id"] is None


def test_put_converters_rejects_branch_b_referencing_branch_a_group(
    client: TestClient, dataset_1: Dataset
) -> None:
    """SelectKBest is SUPERVISED (Branch A: fits independently per fold, may
    legitimately produce different real columns per fold). StandardScaler is
    a plain Branch B converter (fits once on full_dataset and reuses that
    single fitted instance transform-only on every partition). A Branch-B
    converter referencing a Branch-A converter's output group is unsound: it
    would apply one fold's fitted statistics to a different fold's different
    real columns. This must be rejected at config time."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Branch B Referencing Branch A Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "SelectKBest",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                },
                {
                    "id": "conv_1",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "conv_0", "slot": 0}
                    ],
                },
            ]
        },
    )
    assert response.status_code == 422


def test_put_converters_accepts_branch_a_referencing_branch_b_group(
    client: TestClient, dataset_1: Dataset
) -> None:
    """The reverse direction is fine: a Branch-A (SUPERVISED) converter
    fits independently per partition/fold anyway, so referencing a
    Branch-B converter's group (which resolves to the same real columns on
    every partition) is sound."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Branch A Referencing Branch B Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                },
                {
                    "id": "conv_1",
                    "converter": "SelectKBest",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "conv_0", "slot": 0}
                    ],
                },
            ]
        },
    )
    assert response.status_code == 200


def test_put_converters_rejects_negative_slot(
    client: TestClient, dataset_1: Dataset
) -> None:
    """A negative slot must not be treated as a valid bounds-checked index
    (Python would silently resolve `slots[-1]` to the last slot instead of
    rejecting it); it has to be rejected at config time just like an
    out-of-range positive slot."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Negative Slot Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                },
                {
                    "id": "conv_1",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "conv_0", "slot": -1}
                    ],
                },
            ]
        },
    )
    assert response.status_code == 422


def test_put_converters_resets_stale_preprocessing_state(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Nothing re-runs the real preprocessing job until the wizard
    finalizes (Task 5), so if a session was already preprocessed once
    (FINISHED, with a preprocessed_path) and the user then edits the
    converter list again through this same endpoint (the wizard's "back"
    flow), the stale FINISHED status / preprocessed_path / huey id must be
    cleared, not left pointing at data that no longer reflects the edited
    list."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Stale Preprocessing Reset Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    # Simulate a session that already finished a real preprocessing run.
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        from DashAI.back.core.enums.status import SessionPreprocessingStatus

        model_session = db.get(ModelSession, model_session_id)
        model_session.preprocessing_status = SessionPreprocessingStatus.FINISHED
        model_session.preprocessed_path = "/some/stale/path"
        model_session.preprocessing_huey_id = "some-stale-huey-id"
        db.commit()

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalWidthCm"}],
                }
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["preprocessing_status"] == 0  # NOT_STARTED
    assert body["preprocessed_path"] is None
    assert body["preprocessing_huey_id"] is None


def test_patch_sets_input_output_columns(
    client: TestClient, dataset_1: Dataset
) -> None:
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Patch Columns Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": "{}",
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={
            "input_columns": json.dumps(["a", "b"]),
            "output_columns": json.dumps(["c"]),
        },
    )
    assert response.status_code == 200
    assert response.json()["input_columns"] == ["a", "b"]
    assert response.json()["output_columns"] == ["c"]


def test_patch_splits_no_longer_invalidates_existing_converters(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Converters reference `input_scope` atoms, not real names tied to a
    specific split shape, so a splits change alone no longer clears them
    (see `test_changing_splits_no_longer_invalidates_converters` above for
    the same behavior exercised through the newer converters payload)."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Invalidation Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    changed_splits = dict(HOLDOUT_SPLITS, train=0.5, test=0.3, validation=0.2, seed=7)
    response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={"splits": json.dumps(changed_splits)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["converters_invalidated"] is False
    assert len(body["converters"]) == 1


def test_validate_columns_against_preprocessed_state(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Regression test for the `/model-session/validation` endpoint's
    still-live `partition_is_split` branch: once a session with converters
    has actually finalized (real preprocessing done, not just configured),
    the endpoint must read the real transformed columns off disk rather
    than the raw dataset. Preprocessing now only runs at session creation
    (input/output columns are set up front here), not via a separate PUT
    `/converters` call, per the redesign that moved fitting out of the
    wizard's Preprocessing step."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Validate Against Preprocessed Test",
            "input_columns": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
            "output_columns": [{"kind": "column", "name": "Species"}],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "PCA",
                    "params": {"n_components": 2},
                    "input_scope": [
                        {"kind": "column", "name": name} for name in INPUT_COLUMNS
                    ],
                }
            ],
        },
    )
    assert create_response.status_code == 201, create_response.text
    model_session_id = create_response.json()["id"]
    assert create_response.json()["preprocessing_status"] == 3  # FINISHED

    # A PCA component name doesn't exist in the raw dataset — validating
    # against it without model_session_id would 400/error; with it, the
    # preprocessed columns (2 PCA components + Species) are used instead.
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_1.id,
            "model_session_id": model_session_id,
            "inputs_columns": ["pca0", "pca1"],
            "outputs_columns": ["Species"],
        },
    )
    assert response.status_code == 200
    assert response.json()["dataset_status"] == "valid"


def test_finalize_columns_enqueues_preprocessing_job_when_converters_present(
    client: TestClient, dataset_1: Dataset
) -> None:
    """End-to-end regression test for the enqueue-after-commit fix: the
    `SessionPreprocessingJob` this PATCH enqueues opens its own DB session
    when it runs, so it only sees this same request's finalized
    `input_columns`/`output_columns` if they were actually committed
    *before* the job is put on the queue. Asserting on `preprocessing_status`
    /`preprocessing_huey_id` alone can't tell the two orderings apart (both
    produce a non-null huey id and a terminal status either way); only the
    real saved partition's columns can, so this loads it back and checks it
    reflects the finalized selection, not the raw dataset's untouched
    columns from before this PATCH.

    Uses literal `{"kind": "column", ...}` atoms for both input and output,
    not a converter output `group` atom: a `group` atom's real column
    names/count aren't resolvable pre-fit (see
    `dataset_split_utils._atom_names_if_all_columns`), so
    `load_dataset_and_splitter` always falls back to its "whole dataset as
    X, placeholder Y" path for *any* group atom regardless of whether the
    session's row was committed before or after the job ran — i.e. a group
    atom can't distinguish the two orderings either (verified empirically:
    both produce the same 5-raw-column save). That gap is pre-existing
    (`group_registry`, returned by `apply_session_converters`, is captured
    in `SessionPreprocessingJob.run()` but never consulted to resolve a
    session's own group atoms after a real fit) and out of scope here."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Finalize Enqueue Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={
            "input_columns": json.dumps([{"kind": "column", "name": "SepalLengthCm"}]),
            "output_columns": json.dumps([{"kind": "column", "name": "Species"}]),
        },
    )
    assert response.status_code == 200
    body = response.json()
    # The job runs synchronously in test mode (huey `immediate=True`), and
    # this endpoint refreshes `model_session` after enqueuing it, so the
    # response already reflects the job's terminal status.
    assert body["preprocessing_status"] == 3  # FINISHED
    assert body["preprocessing_huey_id"] is not None

    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        train_path = os.path.join(model_session.preprocessed_path, "train")
        # The partition is saved as two separate datasets, `x`/`y` (see
        # `SessionPreprocessingJob.run()`), not one combined dataset.
        x_saved = load_dataset(os.path.join(train_path, "x"))
        y_saved = load_dataset(os.path.join(train_path, "y"))

    # Proves the job saw THIS request's just-finalized columns, not the
    # stale pre-finalize ones (`[]`/`[]`): a stale read forces the
    # placeholder path (whole 5-column raw dataset saved as x, output
    # discarded — reproduced manually while investigating this fix),
    # whereas a correct, post-commit read produces exactly the two
    # finalized columns, one per saved file.
    assert x_saved.column_names == ["SepalLengthCm"]
    assert y_saved.column_names == ["Species"]

    # And the saved SepalLengthCm values are the StandardScaler's *fitted*
    # output (zero mean), not the untouched raw column — proving the
    # converter this same request applied was actually exercised on the
    # finalized selection, not skipped/bypassed.
    scaled = list(x_saved["SepalLengthCm"])
    assert abs(sum(scaled) / len(scaled)) < 1e-6


def test_patch_on_already_finalized_session_does_not_reenqueue_job(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Regression test for the Bug 2 fix regression found in review round 2:
    the enqueue guard must require BOTH that THIS SAME call is the one
    setting input_columns/output_columns AND that the resulting values are
    non-empty — not just the latter. A guard that only checks the
    session's current (already-finalized) content would re-enqueue a full
    preprocessing job on ANY later successful PATCH, even one that never
    touches input_columns/output_columns at all (a bare rename, or a
    splits/strategy-only change), which the brief explicitly rules out
    ("cuando esta misma llamada fija input_columns/output_columns... no en
    cualquier otra llamada, como el cambio de split")."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "No Reenqueue Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    finalize_response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={
            "input_columns": json.dumps([{"kind": "column", "name": "SepalLengthCm"}]),
            "output_columns": json.dumps([{"kind": "column", "name": "Species"}]),
        },
    )
    assert finalize_response.status_code == 200
    finalize_body = finalize_response.json()
    assert finalize_body["preprocessing_status"] == 3  # FINISHED
    first_huey_id = finalize_body["preprocessing_huey_id"]
    assert first_huey_id is not None

    # A later call that touches only an unrelated field (name) on an
    # already-finalized session must not enqueue a new job: the huey id
    # must stay exactly the one the finalize call above produced.
    rename_response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={"name": "Renamed After Finalize"},
    )
    assert rename_response.status_code == 200
    rename_body = rename_response.json()
    assert rename_body["name"] == "Renamed After Finalize"
    assert rename_body["preprocessing_huey_id"] == first_huey_id
    assert rename_body["preprocessing_status"] == 3  # still FINISHED, unchanged

    # Same for a splits-only change: converters/input_columns/output_columns
    # already exist, but this call itself doesn't set input_columns/
    # output_columns, so it must not re-trigger preprocessing either.
    changed_splits = dict(HOLDOUT_SPLITS, train=0.5, test=0.3, validation=0.2, seed=11)
    splits_response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={"splits": json.dumps(changed_splits)},
    )
    assert splits_response.status_code == 200
    splits_body = splits_response.json()
    assert splits_body["preprocessing_huey_id"] == first_huey_id
    assert splits_body["preprocessing_status"] == 3


def test_changing_splits_no_longer_invalidates_converters(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Converters reference input_scope atoms, not real names tied to a
    specific split shape, so a split change no longer needs to clear them."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Split Change Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]
    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={"splits": json.dumps(HOLDOUT_SPLITS)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["converters_invalidated"] is False
    assert len(body["converters"]) == 1


def test_create_model_session_rejects_invalid_converter_config(
    client: TestClient, dataset_1: Dataset
) -> None:
    """POST /model-session/ must run the same converters validation the PUT
    /converters endpoint runs, so a session created directly with an invalid
    converters list is rejected with 422 before any DB write, instead of
    silently persisting an unsound configuration."""
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "POST Invalid Converters Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "does_not_exist"}],
                }
            ],
        },
    )
    assert response.status_code == 422


def test_create_model_session_with_converters_and_finalized_columns_enqueues_job(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Regression test for the `create_model_session` atom-serialization
    bug: `params.input_columns`/`output_columns` are `List[ColumnAtom]`
    (pydantic objects) since Task 2, and the `ModelSession.input_columns`/
    `output_columns` DB columns are plain JSON — assigning the pydantic
    objects directly used to raise an uncaught
    `TypeError: Object of type ColumnAtom is not JSON serializable` at
    `db.commit()`, surfacing as an unhandled 500. A session created with a
    valid, non-empty `converters` list AND non-empty, already-finalized
    `input_columns`/`output_columns` atoms must succeed (201) and actually
    enqueue+finish the preprocessing job right away (same as
    `update_model_session` does when it finalizes columns on an existing
    session with converters already configured)."""
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "POST With Atoms And Converters Test",
            "input_columns": [{"kind": "column", "name": "SepalLengthCm"}],
            "output_columns": [{"kind": "column", "name": "Species"}],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["input_columns"] == [
        {"kind": "column", "name": "SepalLengthCm", "converter_id": None, "slot": None}
    ]
    assert body["output_columns"] == [
        {"kind": "column", "name": "Species", "converter_id": None, "slot": None}
    ]
    # Runs synchronously in test mode, so the response already reflects the
    # job's terminal status.
    assert body["preprocessing_status"] == 3  # FINISHED
    assert body["preprocessing_huey_id"] is not None
    assert body["preprocessed_path"] is not None


def test_put_converters_rejects_group_from_converter_without_output_slots(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Some converters (the imbalanced-learn samplers) raise
    `NotImplementedError` from `get_output_type()`, which the default
    `get_output_slots()` calls — so a later, non-fit-once converter
    referencing one of them as a `group` used to blow up with an unhandled
    500. It must be a clean 422 naming the offending converter instead."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Undeclarable Output Slots Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "SMOTEConverter",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                    "target_column": "Species",
                },
                # SelectKBest is SUPERVISED (so it is *not* "fit once", and
                # the fit-once/fits-per-partition guard doesn't fire first);
                # it reaches the output-slot resolution directly.
                {
                    "id": "conv_1",
                    "converter": "SelectKBest",
                    "params": {},
                    "input_scope": [
                        {"kind": "group", "converter_id": "conv_0", "slot": 0}
                    ],
                    "target_column": "Species",
                },
            ]
        },
    )
    assert response.status_code == 422
    assert "output structure" in response.json()["detail"]
    assert "conv_0" in response.json()["detail"]


def test_patch_rejects_group_atom_as_output_column(
    client: TestClient, dataset_1: Dataset
) -> None:
    """A converter's output group can never be the session's target: the
    raw dataset is split before any converter runs. The preprocessing job
    already refuses it, but only asynchronously — the wizard needs the same
    rejection synchronously, when it finalizes the session."""
    create_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "Group Atom As Target Test",
            "input_columns": [],
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(HOLDOUT_SPLITS),
        },
    )
    model_session_id = create_response.json()["id"]

    client.put(
        f"/api/v1/model-session/{model_session_id}/converters",
        json={
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
                }
            ]
        },
    )

    response = client.patch(
        f"/api/v1/model-session/{model_session_id}",
        params={
            "input_columns": json.dumps([{"kind": "column", "name": "SepalLengthCm"}]),
            "output_columns": json.dumps(
                [{"kind": "group", "converter_id": "conv_0", "slot": 0}]
            ),
        },
    )
    assert response.status_code == 422
    assert "group output" in response.json()["detail"]

    # And nothing was persisted / enqueued: the session's own columns are
    # untouched and no preprocessing job was started.
    session_response = client.get(f"/api/v1/model-session/{model_session_id}")
    assert session_response.json()["output_columns"] == []
    assert session_response.json()["preprocessing_status"] in (None, 0)


def test_converters_output_slots_reflects_real_params_not_defaults(
    client: TestClient,
) -> None:
    """`SimpleImputer` only declares a second `missing_indicator` slot when
    `add_indicator=True`. The generic `/component/SimpleImputer/` metadata
    always reflects the schema's *default* (`add_indicator=False`), so the
    wizard's atom list needs this endpoint to see a specific converter
    instance's real, session-configured params instead."""
    response = client.post(
        "/api/v1/model-session/converters/output-slots",
        json={
            "converters": [
                {
                    "id": "conv_default",
                    "converter": "SimpleImputer",
                    "params": {},
                },
                {
                    "id": "conv_with_indicator",
                    "converter": "SimpleImputer",
                    "params": {"add_indicator": True},
                },
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    default_slots = body["conv_default"]
    assert len(default_slots) == 1
    assert default_slots[0]["label"] == "imputed"

    with_indicator_slots = body["conv_with_indicator"]
    assert len(with_indicator_slots) == 2
    labels = [s["label"] for s in with_indicator_slots]
    assert "imputed" in labels
    assert "missing_indicator" in labels
    indicator_slot = next(
        s for s in with_indicator_slots if s["label"] == "missing_indicator"
    )
    assert indicator_slot["type"] == "Integer"
