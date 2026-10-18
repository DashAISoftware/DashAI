import pytest
from fastapi.testclient import TestClient
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests

from DashAI.back.dependencies.database.models import Dataset, ModelSession


@pytest.fixture(name="model_session_id")
def create_model_session_id(client: TestClient, dataset_1: Dataset):
    """Create a model session that can own saved statistical test rows."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="statistical-tests-session",
            task_name="TabularClassificationTask",
            input_columns=["SepalLengthCm", "SepalWidthCm"],
            output_columns=["Species"],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="holdout",
            splits={
                "train": 0.8,
                "test": 0.2,
                "validation": 0.0,
                "seed": 42,
                "shuffle": True,
                "stratify": False,
            },
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        yield model_session.id
        db.delete(model_session)
        db.commit()


def test_run_statistical_test_returns_result(client: TestClient):
    """The endpoint should run a supported statistical test and return metadata."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {
                "1": [0.7, 0.8, 0.9, 0.95],
                "2": [0.2, 0.3, 0.4, 0.4],
            },
            "alpha": 0.05,
            "params": {"alternative": "two-sided"},
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["test_name"] == "PairedTTest"
    assert data["significant"] is True
    assert data["p_value"] is not None
    assert data["statistic"] is not None
    assert data["details"]["scores"] == {
        "1": [0.7, 0.8, 0.9, 0.95],
        "2": [0.2, 0.3, 0.4, 0.4],
    }


def test_run_statistical_test_rejects_empty_fold_metrics(client: TestClient):
    """The endpoint should reject empty fold_metrics payloads."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "fold_metrics cannot be empty"


def test_run_statistical_test_rejects_unknown_test(client: TestClient):
    """The endpoint should reject unknown statistical test names."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "UnknownTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {"1": [1.0, 2.0], "2": [2.0, 1.0]},
        },
    )

    assert response.status_code == 400
    assert "Unknown statistical test" in response.json()["detail"]


def _run_test(client: TestClient, test_name: str, fold_metrics: dict, params=None):
    """Run a statistical test through the API with default request fields."""
    return client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": test_name,
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [int(run_id) for run_id in fold_metrics],
            "run_names": {run_id: f"Run{run_id}" for run_id in fold_metrics},
            "fold_metrics": fold_metrics,
            "alpha": 0.05,
            "params": params or {},
        },
    )


SCORES_A = [0.8, 0.82, 0.85, 0.81, 0.83]
# SCORES_A - 0.1 written as literals: the differences carry floating-point
# noise, so their variance is ~1e-34 instead of exactly 0
SCORES_A_SHIFTED = [0.7, 0.72, 0.75, 0.71, 0.73]
SCORES_B = [0.71, 0.72, 0.77, 0.70, 0.73]
SCORES_C = [0.60, 0.66, 0.61, 0.64, 0.62]


@pytest.mark.parametrize(
    ("test_name", "fold_metrics", "params", "expected_detail"),
    [
        (
            "AnovaTest",
            {"1": [0.9] * 5, "2": [0.9] * 5, "3": [0.9] * 5},
            {},
            "ANOVA is undefined",
        ),
        (
            "FriedmanTest",
            {"1": SCORES_A, "2": SCORES_A, "3": SCORES_A},
            {},
            "Friedman Test is undefined",
        ),
        ("ShapiroTest", {"1": [0.9] * 5}, {}, "Shapiro-Wilk Test is undefined"),
        ("ShapiroTest", {"1": [0.8, 0.9]}, {}, "at least three folds"),
        (
            "LeveneTest",
            {"1": [0.8, 0.9], "2": [0.7, 0.75], "3": [0.6, 0.9]},
            {},
            "Levene's Test is undefined",
        ),
        (
            "LeveneTest",
            {"1": [0.9] * 5, "2": [0.8] * 5},
            {},
            "Levene's Test is undefined",
        ),
        (
            "BartlettTest",
            {"1": [0.9] * 5, "2": [0.8] * 5},
            {},
            "Bartlett's Test is undefined",
        ),
        (
            "PairedTTest",
            {"1": SCORES_A, "2": SCORES_A_SHIFTED},
            {"alternative": "two-sided"},
            "differ by exactly the same amount",
        ),
        (
            "CorrectedPairedTTest",
            {"1": SCORES_A, "2": SCORES_A_SHIFTED},
            {"alternative": "two-sided"},
            "differ by exactly the same amount",
        ),
        (
            # Every pair differs by a constant: nothing can be shown per row
            "PairedTTest",
            {"1": [0.9] * 5, "2": [0.8] * 5, "3": [0.7] * 5},
            {"alternative": "two-sided", "correction_method": "holm"},
            "None of the pairs of models could be compared",
        ),
    ],
)
def test_run_statistical_test_rejects_undefined_results(
    client: TestClient, test_name, fold_metrics, params, expected_detail
):
    """Degenerate scores should return an explanatory 400 instead of a NaN
    result, which would otherwise be reported as "not significant"."""
    response = _run_test(client, test_name, fold_metrics, params)

    assert response.status_code == 400, response.text
    assert expected_detail in response.json()["detail"]
    assert not response.json()["detail"].startswith("Error running")


@pytest.mark.parametrize("test_name", ["PairedTTest", "CorrectedPairedTTest"])
def test_t_tests_report_identical_runs_as_not_significant(
    client: TestClient, test_name
):
    """Two runs with identical scores show no difference (p = 1)."""
    response = _run_test(
        client, test_name, {"1": SCORES_A, "2": SCORES_A}, {"alternative": "less"}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["statistic"] == 0.0
    assert data["p_value"] == 1.0
    assert data["significant"] is False


@pytest.mark.parametrize("test_name", ["PairedTTest", "CorrectedPairedTTest"])
def test_t_tests_keep_other_pairs_when_two_runs_are_identical(
    client: TestClient, test_name
):
    """An identical pair must not abort the remaining pairwise comparisons."""
    response = _run_test(
        client,
        test_name,
        {"1": SCORES_A, "2": SCORES_A, "3": SCORES_B},
        {"alternative": "two-sided", "correction_method": "holm"},
    )

    assert response.status_code == 200, response.text
    pairs = {
        (pair["run_1"], pair["run_2"]): pair for pair in response.json()["posthoc"]
    }
    assert pairs[(1, 2)]["p_value"] == 1.0
    assert pairs[(1, 2)]["significant"] is False
    assert pairs[(1, 3)]["p_value"] < 1.0
    assert pairs[(2, 3)]["p_value"] < 1.0


def test_paired_t_test_reports_undefined_pair_in_its_row(
    client: TestClient, model_session_id: int
):
    """A pair with a constant non-zero difference gets an error in its row;
    the other pairs are computed and corrected without it, and the row error
    survives saving the result."""
    response = _run_test(
        client,
        "PairedTTest",
        {"1": SCORES_A, "2": SCORES_A_SHIFTED, "3": SCORES_C},
        {"alternative": "two-sided", "correction_method": "holm"},
    )

    assert response.status_code == 200, response.text
    pairs = {
        (pair["run_1"], pair["run_2"]): pair for pair in response.json()["posthoc"]
    }
    assert pairs[(1, 2)]["p_value"] is None
    assert pairs[(1, 2)]["significant"] is False
    assert "zero variance" in pairs[(1, 2)]["error"]

    # Holm over the two computable pairs only
    raw_p_values = [
        ttest_rel(SCORES_A, SCORES_C).pvalue,
        ttest_rel(SCORES_A_SHIFTED, SCORES_C).pvalue,
    ]
    expected = multipletests(raw_p_values, method="holm")[1]
    assert pairs[(1, 3)]["p_value"] == pytest.approx(expected[0])
    assert pairs[(2, 3)]["p_value"] == pytest.approx(expected[1])
    assert pairs[(1, 3)]["error"] is None

    # posthoc is stored as free-form JSON, so the row error round-trips
    data = response.json()
    save_response = client.post(
        "/api/v1/statistical-tests/save",
        json=[
            {
                "test_name": "PairedTTest",
                "metric_name": "accuracy",
                "metric_split": "test",
                "alpha": data["alpha"],
                "significant": data["significant"],
                "posthoc": data["posthoc"],
                "model_session_id": model_session_id,
            }
        ],
    )
    assert save_response.status_code == 201, save_response.text
    saved = save_response.json()[0]
    assert saved["posthoc"] == data["posthoc"]

    client.delete(f"/api/v1/statistical-tests/saved/{saved['id']}")


def test_infinite_statistic_is_sent_and_saved_as_string(
    client: TestClient, model_session_id: int
):
    """Constant but different models give F = inf, which JSON cannot encode;
    it must reach the frontend as "Infinity" instead of null."""
    response = _run_test(
        client, "AnovaTest", {"1": [0.9] * 5, "2": [0.8] * 5, "3": [0.7] * 5}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["statistic"] == "Infinity"
    assert data["p_value"] == 0.0
    assert data["significant"] is True

    save_response = client.post(
        "/api/v1/statistical-tests/save",
        json=[
            {
                "test_name": "AnovaTest",
                "metric_name": "accuracy",
                "metric_split": "test",
                "alpha": 0.05,
                "significant": True,
                "statistic": data["statistic"],
                "p_value": data["p_value"],
                "model_session_id": model_session_id,
            }
        ],
    )
    assert save_response.status_code == 201, save_response.text
    saved = save_response.json()[0]
    assert saved["statistic"] == "Infinity"

    client.delete(f"/api/v1/statistical-tests/saved/{saved['id']}")


def test_tukey_reports_identical_constant_runs_as_not_significant(
    client: TestClient,
):
    """With every run constant, Tukey's standard error is 0: identical runs
    give 0/0 and must be reported as p = 1 instead of a null p-value."""
    response = _run_test(
        client, "AnovaTest", {"3": [1.0] * 5, "4": [0.5] * 5, "7": [0.5] * 5}
    )

    assert response.status_code == 200, response.text
    pairs = {
        (pair["run_1"], pair["run_2"]): pair for pair in response.json()["posthoc"]
    }
    assert pairs[(3, 4)]["p_value"] == 0.0
    assert pairs[(3, 4)]["significant"] is True
    assert pairs[(3, 7)]["p_value"] == 0.0
    assert pairs[(4, 7)]["p_value"] == 1.0
    assert pairs[(4, 7)]["significant"] is False


def test_significant_friedman_runs_nemenyi_posthoc(client: TestClient):
    """A significant Friedman test must come back with the Nemenyi pairs, in
    the right order and with identical runs reported as p = 1."""
    response = _run_test(
        client,
        "FriedmanTest",
        # Keys deliberately unsorted: best is 3, then 1 and 2 (identical)
        {"3": [0.9] * 10, "1": [0.7] * 10, "2": [0.7] * 10},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["significant"] is True
    pairs = {(pair["run_1"], pair["run_2"]): pair for pair in data["posthoc"]}
    assert set(pairs) == {(3, 1), (3, 2), (1, 2)}
    assert pairs[(3, 1)]["significant"] is True
    assert pairs[(3, 2)]["significant"] is True
    assert pairs[(1, 2)]["p_value"] == pytest.approx(1.0)
    assert pairs[(1, 2)]["significant"] is False


# One unit in the last place of 0.5: the size of the noise left by averaging
# or summing metrics in a different order
ULP = 2**-53


def test_friedman_ignores_floating_point_noise(client: TestClient):
    """Three runs equal up to 1-2 ulps used to be ranked consistently by the
    noise, giving p ~ 0.005 instead of the p ~ 0.75 of the exact scores."""
    other = [0.49, 0.51, 0.49, 0.51, 0.49, 0.51, 0.51, 0.49, 0.49, 0.51]
    noisy = _run_test(
        client,
        "FriedmanTest",
        {
            "1": [0.5] * 10,
            "2": [0.5 + ULP] * 10,
            "3": [0.5 + 2 * ULP] * 10,
            "4": other,
        },
    )
    exact = _run_test(
        client,
        "FriedmanTest",
        {"1": [0.5] * 10, "2": [0.5] * 10, "3": [0.5] * 10, "4": other},
    )

    assert noisy.status_code == 200, noisy.text
    assert noisy.json()["significant"] is False
    assert noisy.json()["p_value"] == pytest.approx(exact.json()["p_value"])


def test_tukey_ignores_floating_point_noise(client: TestClient):
    """Nearly constant runs make Tukey's standard error ~1e-17, so runs equal
    up to a few ulps used to come out as significantly different."""
    response = _run_test(
        client,
        "AnovaTest",
        {
            "1": [0.5, 0.5 + ULP, 0.5 - ULP, 0.5, 0.5],
            "2": [0.5 + 2 * ULP, 0.5 + ULP, 0.5 + ULP, 0.5 + ULP, 0.5 + ULP],
            "3": [1.0] * 5,
        },
    )

    assert response.status_code == 200, response.text
    pairs = {
        (pair["run_1"], pair["run_2"]): pair for pair in response.json()["posthoc"]
    }
    assert pairs[(1, 2)]["p_value"] == 1.0
    assert pairs[(1, 2)]["significant"] is False
    assert pairs[(1, 3)]["significant"] is True


def test_save_list_and_delete_statistical_tests(
    client: TestClient, model_session_id: int
):
    """Saved results should be stored, listed, and removed through the API."""
    payload = [
        {
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "alpha": 0.05,
            "significant": True,
            "name": "First result",
            "description": "Saved from the API",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "statistic": 2.75,
            "p_value": 0.01,
            "interpretation": "Significant",
            "params": {"alternative": "two-sided"},
            "details": {"folds": 4},
            "posthoc": [],
            "model_session_id": model_session_id,
        },
        {
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "validation",
            "alpha": 0.05,
            "significant": False,
            "name": "Second result",
            "description": "Saved from the API",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "statistic": 0.5,
            "p_value": 0.6,
            "interpretation": "Not significant",
            "params": {"alternative": "two-sided"},
            "details": {"folds": 4},
            "posthoc": [],
            "model_session_id": model_session_id,
        },
    ]

    save_response = client.post(
        "/api/v1/statistical-tests/save",
        json=payload,
    )
    assert save_response.status_code == 201, save_response.text
    saved_items = save_response.json()
    assert len(saved_items) == 2
    assert saved_items[0]["model_session_id"] == model_session_id
    assert saved_items[1]["model_session_id"] == model_session_id
    assert saved_items[0]["group_id"] == saved_items[1]["group_id"]

    list_response = client.get(
        f"/api/v1/statistical-tests/saved?model_session_id={model_session_id}"
    )
    assert list_response.status_code == 200, list_response.text
    listed_items = list_response.json()
    assert len(listed_items) >= 2
    assert any(item["name"] == "First result" for item in listed_items)

    group_id = saved_items[0]["group_id"]
    filtered_response = client.get(
        f"/api/v1/statistical-tests/saved?group_id={group_id}"
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered_items = filtered_response.json()
    assert len(filtered_items) == 2

    delete_response = client.delete(
        f"/api/v1/statistical-tests/saved/{saved_items[0]['id']}"
    )
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json() == {
        "deleted": True,
        "id": saved_items[0]["id"],
    }

    remaining_response = client.get(
        f"/api/v1/statistical-tests/saved?model_session_id={model_session_id}"
    )
    assert remaining_response.status_code == 200
    remaining_items = remaining_response.json()
    assert all(item["id"] != saved_items[0]["id"] for item in remaining_items)
